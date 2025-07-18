"""
main.py - AI-Powered Weekly GitHub Activity to Notion Posts

This script automates the process of:
1. Fetching the last 7 days of GitHub activity (commits and pull requests) for a user.
2. Summarizing the activity for AI input.
3. Using OpenAI GPT to generate LinkedIn post topics and full posts.
4. Saving the generated posts to a Notion database for review and scheduling.

Environment Variables Required:
- PERSONAL_GITHUB_TOKEN: GitHub Personal Access Token
- PERSONAL_GITHUB_USERNAME: GitHub username
- OPENAI_API_KEY: OpenAI API key
- NOTION_TOKEN: Notion integration token
- NOTION_DATABASE_ID: Notion database ID

Usage:
Run this script manually or via GitHub Actions for weekly automation.
"""

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

# Validate environment variables
for var in [PERSONAL_GITHUB_TOKEN, PERSONAL_GITHUB_USERNAME, OPENAI_API_KEY, NOTION_TOKEN, NOTION_DATABASE_ID]:
    if not var:
        raise ValueError("All required environment variables must be set.")


openai.api_key = OPENAI_API_KEY


def fetch_github_activity(username, token):
    """
    Fetches recent GitHub activity (PushEvent and PullRequestEvent) for a given user within the last 7 days.

    Args:
        username (str): GitHub username to fetch activity for.
        token (str): GitHub personal access token for authentication.

    Returns:
        list: A list of dictionaries, each representing an activity event with the following keys:
            - repo (str): Repository name where the event occurred.
            - type (str): Type of the event ("PushEvent" or "PullRequestEvent").
            - desc (str): Short description of the event.
            - created_at (str): ISO formatted timestamp of when the event was created.
            - body (str): Detailed message or body of the event (commit messages or PR body).

    Raises:
        requests.HTTPError: If the GitHub API request fails.
    """
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    since = (datetime.now() - timedelta(days=7)).isoformat() + "Z"
    events_url = f"https://api.github.com/users/{username}/events?per_page=100"
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
    """
    Summarizes a list of activity events from the last 7 days.

    Args:
        activity (list): A list of dictionaries, each representing an activity event.
            Each dictionary should contain the keys:
                - 'type': The type of event ('PushEvent' or 'PullRequestEvent').
                - 'desc': A description of the event.
                - 'repo': The repository name associated with the event.
                - 'body': The content or details of the event.

    Returns:
        str: A formatted summary string of the activity events. If no activity is found,
            returns "No activity found in the last 7 days."
    """
    
    if not activity:
        return "No activity found in the last 7 days."
    summary_lines = ["Last week:"]
    for item in activity:
        if item['type'] == 'PushEvent':
            summary_lines.append(f"- {item['desc']} in {item['repo']} with content: {item['body']}")
        elif item['type'] == 'PullRequestEvent':
            summary_lines.append(f"- Merged {item['desc']} in {item['repo']} with content: {item['body']}")
    return "\n".join(summary_lines)


def generate_linkedin_post_ideas(summary):
    """
    Generates five unique LinkedIn post ideas based on a provided weekly GitHub activity summary.

    Args:
        summary (str): A textual summary of weekly GitHub activity.

    Returns:
        str: A JSON-formatted string containing five post ideas. Each idea includes:
            - heading: A short title for the post.
            - body: A detailed explanation suitable for a LinkedIn post.

    Notes:
        - The response does not include emojis.
        - The JSON is not wrapped in markdown or additional text.
    """
    
    prompt = f"""
You are a social media marketer.

Task:
- List 5 unique topics that I worked on that can be turned into LinkedIn posts based on the following weekly GitHub activity summary.

Note:
- Donot add any emojis
- Provide the response in a JSON format with the following structure with no markdown. Donot wrap the JSON response in any other text or markdown or code blocks:
- heading: A short title for the post
- body: A detailed explanation of the topic suitable for a LinkedIn post

Summary:
{summary}
"""
    response = openai.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "system", "content": "You are a helpful assistant."},
                  {"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def generate_linkedin_post(brief):
    """
    Generates a personalized LinkedIn post based on a provided brief using OpenAI's GPT model.

    Args:
        brief (str): A short description or summary of the topic for the LinkedIn post.

    Returns:
        str: The generated LinkedIn post body, written in first person, with storytelling elements, simple and engaging language, and optionally emojis or humor.
    """
    
    prompt = f"""
You are a social media marketer and a good story writer who has good technical and coding knowledge.

Your tasks:
- Based on the following brief, create a LinkedIn post.
- Make it personal and add story-telling. 
- Also, add reasons supporting why would I have done this.

Notes:
- Always write in first person and write like a human not like a bot
- Be free to add emojis and very tiny bit of humor if relevant.
- Only provide the post body without any markdown.
- Donot wrap the JSON response in any other text or markdown or code blocks.
- Keep the lanaguage simple, professional yet engaging.

Brief:
{brief}
"""
    response = openai.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "system", "content": "You are a helpful assistant."},
                  {"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def add_post_to_notion(post, topic,  date):
    """
    Adds a post to a Notion database as a new page.
    Args:
        post (dict): A dictionary containing post details, including 'heading' and 'body'.
        topic (str): The topic or main content of the post.
        date (str): The due date for the post in ISO format (YYYY-MM-DD).
    Returns:
        None
    Side Effects:
        Sends a POST request to the Notion API to create a new page.
        Prints a success or failure message based on the API response.
    """
        
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    content = f"Brief:\n\n{post['body']}\n\n---\n\nPost:\n\n{topic}"
    
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
                    "rich_text": [{"type": "text", "text": {"content": content}}]
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
    marketing_posts_json = generate_linkedin_post_ideas(weekly_summary)
    try:
        marketing_posts_topics = json.loads(marketing_posts_json)
    except Exception as e:
        print("Error parsing AI response:", e)
        return
    today = datetime.today()
    for i, topic in enumerate(marketing_posts_topics):
        post = generate_linkedin_post(topic["body"])
        post_date = (today + timedelta(days=i)).strftime('%Y-%m-%d')
        
        print(f"Topic {i+1}:")
        print(topic)
        print(post)
        print(post_date)
        
        add_post_to_notion(topic, post, post_date)

if __name__ == "__main__":
    main()
