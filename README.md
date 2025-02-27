Jira Chatbot 

Overview

Jira Chatbot is an AI-powered assistant that integrates with Jira, allowing users to manage issues, sprints, and tasks through natural language conversations. Built using Streamlit, LangChain, and OpenAI GPT-4, the chatbot can perform various Jira actions like creating issues, updating statuses, fetching sprint details, and more.

Features 🚀

📝 Create Jira Issues (Tasks, Bugs, Stories, etc.)

✅ Close and Update Issue Status

📌 Retrieve Issue Status and Summaries

🗂 List Backlog and Active Sprint Issues

🔄 Move Issues Between Sprint and Backlog

📢 Summarize Last Reported Issue

💬 Interactive Chat Interface with Typing Effect

Tech Stack 🛠

Python 3.x

Streamlit (UI)

LangChain (LLM Integration)

OpenAI GPT-4 Turbo (LLM)

JIRA API (Issue Management)

Installation & Setup 🔧

1️⃣ Clone the Repository

git clone https://github.com/YOUR_GITHUB_USERNAME/jira-chatbot.git
cd jira-chatbot

2️⃣ Create a Virtual Environment (Optional but Recommended)

python -m venv venv
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate  # On Windows

3️⃣ Install Dependencies

pip install -r requirements.txt

4️⃣ Set Up Environment Variables

Create a .env file in the project root and add the following:

JIRA_SERVER=https://your-jira-instance.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token
OPENAI_API_KEY=your-openai-api-key

Alternatively, replace hardcoded values in jira_chatbot.py.

5️⃣ Run the Chatbot

streamlit run jira_chatbot.py

The chatbot UI will open in your browser.

How to Use 🏗

Open the chatbot UI.

Type your message (e.g., "Create a task in project XYZ with summary 'Fix login issue'").

The bot processes the request and executes the action in Jira.

View issue details, backlog, sprint statuses, or update issues as needed.

Clear chat anytime using the "🗑 Clear Chat" button.

Example Commands ✨

Command

Action

Create a bug in project ABC with summary 'Fix crash on startup'

Creates a new bug in Jira

Close issue ABC-123

Closes issue ABC-123

What is the status of issue XYZ-456?

Retrieves the status of XYZ-456

Summarize my last reported issue

Summarizes the most recent issue created by the user

List backlog issues in project DEF

Displays backlog issues for DEF project

Move issue GHI-789 to sprint

Moves issue GHI-789 to the active sprint
