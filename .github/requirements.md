# Weekly GitHub Activity → Weekday Marketing Content → Notion DB

## 📌 Project Goal

Automatically generate **5 unique marketing posts (Mon–Fri)** based on the previous week's GitHub activity, and save them to a Notion database for review and scheduling.

---

## ✅ Features & Workflow

### 1. **Fetch GitHub Activity**

- Use **GitHub REST API** to fetch:
  - Commits (Push Events)
  - Pull Requests (PR Events)
  - Issues (Issues Events)
- Filter events from **last 7 days**.
- Group data by:
  - Repository
  - Event type
  - Description/details

---

### 2. **Summarize Weekly Work**

- Aggregate raw GitHub activity into a readable summary for AI.
- Example:

```

Last week:

- Added feature X in repo Y
- Fixed bug Z in repo A
- Merged PR #123 for optimization

```

---

### 3. **Generate Marketing Content**

- Use an **AI model** (e.g., OpenAI GPT) to create unique posts for LinkedIn.

---

### 4. **Save to Notion Database**

- Use **Notion API** to insert posts into a Notion DB with these fields:
- `Date`
- `Content`
- `Platform` (Twitter / LinkedIn)
- `Status` (Draft / Posted)
- Ensure **Notion OAuth or integration token** is stored securely.

---

### 5. **Automation**

- Schedule script to run **every Sunday at 6 PM IST** using:
- **GitHub Actions** (preferred)
- or Local cron job
- Push logs to repo for debugging.

---

## ✅ Tech Stack

- **Language:** Python 3.11+
- **APIs:** GitHub REST API, Notion API, OpenAI API (or similar)
- **Auth:** GitHub PAT, Notion Integration Token
- **Deployment:** GitHub Actions (for automation)

---

## ✅ File Structure

```

project-root/
├── src/
│ ├── github_fetcher.py # Fetch GitHub activity
│ ├── summarizer.py # Summarize weekly work
│ ├── ai_generator.py # Generate content using AI
│ ├── notion_uploader.py # Push posts to Notion
│ └── main.py # Combine all steps
├── tests/
│ ├── test_github_fetcher.py
│ ├── test_summarizer.py
│ ├── test_ai_generator.py
│ ├── test_notion_uploader.py
├── requirements.txt # Dependencies
├── requirements.md # This file
└── README.md

```

---

## ✅ Future Enhancements

- Auto-post to Twitter & LinkedIn via their APIs
- Add images/code snippets in posts
- Add web UI for post review before publishing
- Support multiple GitHub users

---

## ✅ Environment Variables

```

PERSONAL_GITHUB_TOKEN=your-github-pat
PERSONAL_GITHUB_USERNAME=your-username
NOTION_TOKEN=your-notion-integration-token
NOTION_DATABASE_ID=your-database-id
OPENAI_API_KEY=your-openai-key

```

---

## ✅ Example Run

```bash
python src/main.py
```

Expected output:

- 5 posts generated and saved to Notion database

## Notes for Copilot

Whenever some progress is made, update the .github/progress.md file
