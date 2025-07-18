import os
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()
PERSONAL_GITHUB_TOKEN = os.getenv('PERSONAL_GITHUB_TOKEN')
PERSONAL_GITHUB_USERNAME = os.getenv('PERSONAL_GITHUB_USERNAME')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID')

print(PERSONAL_GITHUB_TOKEN)
print(PERSONAL_GITHUB_USERNAME)
print(OPENAI_API_KEY)
print(NOTION_TOKEN)
print(NOTION_DATABASE_ID)
print(os.environ)

# Validate environment variables
for var in [PERSONAL_GITHUB_TOKEN, PERSONAL_GITHUB_USERNAME, OPENAI_API_KEY, NOTION_TOKEN, NOTION_DATABASE_ID]:
    if not var:
        raise ValueError("All required environment variables must be set.")

openai.api_key = OPENAI_API_KEY

def fetch_github_activity(username, token):
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    since = (datetime.now() - timedelta(days=7)).isoformat() + "Z"
    events_url = f"https://api.github.com/users/{username}/events"
    response = requests.get(events_url, headers=headers)
    response.raise_for_status()
    events = response.json()
    events = [event for event in events if event.get("type", "") in ["PushEvent", "PullRequestEvent"]]
    activity = []
    for event in events:
        created_at = event.get("created_at", "")
        if created_at < since:
            continue
        repo = event["repo"]["name"]
        type_ = event["type"]
        desc = ""
        body = ""
        if type_ == "PushEvent":
            desc = f"Pushed {len(event['payload']['commits'])} commit(s)"
            body = "\n".join(commit["message"] for commit in event["payload"]["commits"])
        elif type_ == "PullRequestEvent":
            pr = event["payload"]["pull_request"]
            desc = f"PR: {pr['title']} (#{pr['number']})"
            body = pr.get("body", "")
        else:
            continue
        activity.append({
            "repo": repo,
            "type": type_,
            "desc": desc,
            "created_at": created_at,
            "body": body
        })
    return activity

def summarize_activity(activity):
    if not activity:
        return "No activity found in the last 7 days."
    summary_lines = ["Last week:"]
    for item in activity:
        if item['type'] == 'PushEvent':
            summary_lines.append(f"- {item['desc']} in {item['repo']} with content: {item['body']}")
        elif item['type'] == 'PullRequestEvent':
            summary_lines.append(f"- Merged {item['desc']} in {item['repo']} with content: {item['body']}")
    return "\n".join(summary_lines)

def generate_linkedin_post(summary):
    prompt = f"""
You are a social media marketer.
Based on the following weekly GitHub activity summary, list 5 unique topics that I worked on that can be later turned into LinkedIn posts.
Be free to add emojis and very tiny bit of humor if relevant.

Provide the response in a JSON format with the following structure with no markdown. Donot wrap the JSON response in any other text or markdown or code blocks:
- heading: A short title for the post
- body: A detailed explanation of the topic suitable for a LinkedIn post

Summary:
{summary}
"""
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "You are a helpful assistant."},
                  {"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content

def add_post_to_notion(post, date):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    data = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Title": {"title": [{"text": {"content": post["heading"]}}]},
            "Due Date": {"date": {"start": date}},
            "Status": {"select": {"name": "To Do"}},
            "Type": {"select": {"name": "Marketing"}},
        },
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": post["body"]}}]
                }
            }
        ]
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        print(f"Post '{post['heading']}' added to Notion for {date}.")
    else:
        print(f"Failed to add post for {date}: {response.text}")

def main():
    activity = fetch_github_activity(PERSONAL_GITHUB_USERNAME, PERSONAL_GITHUB_TOKEN)
    weekly_summary = summarize_activity(activity)
    print("Weekly Summary:\n", weekly_summary)
    marketing_posts_json = generate_linkedin_post(weekly_summary)
    try:
        marketing_posts = json.loads(marketing_posts_json)["posts"]
    except Exception as e:
        print("Error parsing AI response:", e)
        return
    today = datetime.today()
    for i, post in enumerate(marketing_posts):
        post_date = (today + timedelta(days=i)).strftime('%Y-%m-%d')
        add_post_to_notion(post, post_date)

if __name__ == "__main__":
    main()
