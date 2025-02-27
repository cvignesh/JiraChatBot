import streamlit as st, time
from jira import JIRA, JIRAError
from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain.tools import tool

# --- Jira API Setup ---
JIRA_SERVER="https://your-jira-instance.atlassian.net"
JIRA_EMAIL="your-email@example.com"
JIRA_API_TOKEN="your-api-token"
OPENAI_API_KEY="your-openai-api-key"

jira_options = {"server": JIRA_SERVER}
jira = JIRA(options=jira_options, basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN))

# --- OpenAI LLM Setup ---
llm = ChatOpenAI(model="gpt-4-turbo", openai_api_key="OPENAI_API_KEY", temperature=0)


@tool
def close_issue(issue_id: str) -> str:
    """Closes a Jira issue given an issue ID, handling errors gracefully."""
    try:
        issue = jira.issue(issue_id)
        transitions = jira.transitions(issue)

        transition_names = [t['name'].lower() for t in transitions]
        print(f"Available transitions for {issue_id}: {transition_names}")

        for transition in transitions:
            if transition['name'].lower() in ["done", "closed"]:
                jira.transition_issue(issue, transition['id'])
                return f"✅ Issue {issue_id} has been closed."

        return f"❌ Could not close issue {issue_id}. Valid transitions: {transition_names}"

    except JIRAError as e:
        return f"❌ Error: {str(e)}"


@tool
def create_issue(project_key: str, summary: str, description: str, issue_type: str = "Task") -> str:
    """Creates a Jira issue given project key, summary, and description."""
    try:
        issue_dict = {
            "project": {"key": project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type},
        }
        new_issue = jira.create_issue(fields=issue_dict)
        return f"🎉 Issue {new_issue.key} created successfully!"

    except JIRAError as e:
        return f"❌ Error: {str(e)}"


@tool
def update_issue_status(issue_id: str, status: str) -> str:
    """Updates a Jira issue status given issue ID and new status."""
    try:
        issue = jira.issue(issue_id)
        transitions = jira.transitions(issue)

        transition_mapping = {t['name'].lower(): t['id'] for t in transitions}
        print(f"Available transitions for {issue_id}: {transition_mapping}")  # Debugging

        if status.lower() in transition_mapping:
            jira.transition_issue(issue, transition_mapping[status.lower()])
            return f"🔄 Issue {issue_id} updated to '{status}'."
        else:
            return f"❌ No valid transition for '{status}'. Available: {list(transition_mapping.keys())}"

    except JIRAError as e:
        return f"❌ Error: {str(e)}"

@tool
def get_issue_status(issue_id: str) -> str:
    """Retrieves the current status of a Jira issue."""
    try:
        issue = jira.issue(issue_id)
        return f"📌 Issue {issue_id} is currently in status: {issue.fields.status.name}"

    except JIRAError as e:
        return f"❌ Error: {str(e)}"

@tool
def summarize_issue(issue_id: str) -> str:
    """Fetches and summarizes a Jira issue given its ID."""
    try:
        issue = jira.issue(issue_id)

        # Extract Key Details
        summary = issue.fields.summary
        description = issue.fields.description or "No description available."
        status = issue.fields.status.name
        comments = [comment.body for comment in getattr(issue.fields.comment, 'comments', [])[-3:]]

        issue_details = f"""
        **Issue ID:** {issue_id}
        **Summary:** {summary}
        **Status:** {status}
        **Description:** {description}
        **Recent Comments:** {comments or 'No recent comments'}
        """

        prompt = f"Summarize the following Jira issue:\n\n{issue_details}"
        response = llm.predict(prompt)

        return f"📌 **Issue Summary for {issue_id}:**\n{response}"

    except JIRAError as e:
        return f"❌ Error: {str(e)}"

@tool
def summarize_last_reported_issue(user_email: str) -> str:
    """Summarizes the last reported Jira issue by a user."""
    try:
        jql_query = f"reporter = '{user_email}' ORDER BY created DESC"
        issues = jira.search_issues(jql_query, maxResults=1)

        if not issues:
            return "❌ No issues found for this user."

        return summarize_issue(issues[0].key)

    except JIRAError as e:
        return f"❌ Error: {str(e)}"

@tool
def get_backlog_issues(project_key: str, max_results: int = 5) -> str:
    """Retrieves backlog issues for a specific project."""
    try:
        # Corrected JQL query to fetch issues in backlog (not assigned to any sprint)
        jql_query = f"project = '{project_key}' AND sprint is EMPTY AND statusCategory != Done ORDER BY created DESC"
        issues = jira.search_issues(jql_query, maxResults=max_results)

        if not issues:
            return f"📂 No backlog issues found in {project_key}."

        issue_list = "\n".join([f"- {issue.key}: {issue.fields.summary}" for issue in issues])
        return f"📂 Backlog Issues in {project_key}:\n{issue_list}"
    except JIRAError as e:
        return f"❌ Error: {str(e)}"

@tool
def get_active_sprint(project_key: str) -> str:
    """Retrieves the active sprint for a given Jira project."""
    try:
        # Get all boards related to the project
        boards = jira.boards(name=project_key)
        if not boards:
            return f"❌ No boards found for project {project_key}."

        board_id = boards[0].id  # Assuming the first board is the main one
        sprints = jira.sprints(board_id)

        # Find an active sprint
        active_sprint = next((sprint for sprint in sprints if sprint.state == "active"), None)

        if not active_sprint:
            return f"⏳ No active sprint found for project {project_key}."

        return f"🚀 Active Sprint in {project_key}: {active_sprint.name} (ID: {active_sprint.id})"

    except JIRAError as e:
        return f"❌ Error: {str(e)}"

@tool
def get_sprint_issues_by_status(project_key: str, status: str = None) -> str:
    """
    Retrieves issues in the current sprint for a project, filtered by status if provided.
    If no status is provided, returns all issues categorized.
    """
    try:
        # Get all boards for the project
        boards = jira.boards(name=project_key)
        if not boards:
            return f"❌ No boards found for project {project_key}."

        board_id = boards[0].id
        sprints = jira.sprints(board_id)

        # Find the active sprint
        active_sprint = next((sprint for sprint in sprints if sprint.state == "active"), None)
        if not active_sprint:
            return f"⏳ No active sprint found for project {project_key}."

        sprint_id = active_sprint.id

        # Build JQL query
        jql_query = f"project = '{project_key}' AND sprint = {sprint_id}"
        if status:
            jql_query += f" AND status = '{status}'"

        jql_query += " ORDER BY status ASC"

        # Fetch issues
        issues = jira.search_issues(jql_query, maxResults=20)

        if not issues:
            return f"📭 No issues found in the active sprint for {project_key} with status '{status or 'All'}'."

        # Format output
        response = f"🚀 **Issues in Active Sprint ({active_sprint.name})**\n"
        if status:
            response += f"🟢 **Status: {status}**\n\n"
            response += "\n".join([f"- {issue.key}: {issue.fields.summary}" for issue in issues]) or "✅ None"
        else:
            # Categorize if no status is given
            status_categories = {"To Do": [], "In Progress": [], "Done": []}
            for issue in issues:
                status_name = issue.fields.status.name
                if "done" in status_name.lower():
                    status_categories["Done"].append(f"{issue.key}: {issue.fields.summary}")
                elif "progress" in status_name.lower():
                    status_categories["In Progress"].append(f"{issue.key}: {issue.fields.summary}")
                else:
                    status_categories["To Do"].append(f"{issue.key}: {issue.fields.summary}")

            response += f"📌 **To Do:**\n" + ("\n".join(status_categories["To Do"]) or "✅ None") + "\n\n"
            response += f"🔄 **In Progress:**\n" + ("\n".join(status_categories["In Progress"]) or "✅ None") + "\n\n"
            response += f"✅ **Done:**\n" + ("\n".join(status_categories["Done"]) or "✅ None")

        return response

    except JIRAError as e:
        return f"❌ Error: {str(e)}"

@tool
def move_issue_sprint_backlog(issue_id: str, project_key: str, move_to: str) -> str:
    """
    Moves an issue between the active sprint and backlog.
    - move_to="backlog" → Moves issue to the backlog.
    - move_to="sprint"  → Moves issue to the active sprint.
    """
    try:
        issue = jira.issue(issue_id)

        # Get all boards for the project
        boards = jira.boards(name=project_key)
        if not boards:
            return f"❌ No boards found for project {project_key}."

        board_id = boards[0].id
        sprints = jira.sprints(board_id)

        # Find the active sprint
        active_sprint = next((sprint for sprint in sprints if sprint.state == "active"), None)

        if move_to.lower() == "backlog":
            # Move issue to backlog by setting the sprint field to None
            jira.issue(issue_id).update(fields={"customfield_10020": None})
            return f"📤 Issue {issue_id} has been moved to the backlog."

        elif move_to.lower() == "sprint":
            if not active_sprint:
                return f"⏳ No active sprint found for project {project_key}."

            # Move issue to active sprint
            jira.issue(issue_id).update(fields={"customfield_10020": active_sprint.id})
            return f"🚀 Issue {issue_id} has been moved to sprint **{active_sprint.name}**."

        else:
            return "❌ Invalid option! Use 'backlog' or 'sprint'."

    except JIRAError as e:
        return f"❌ Error: {str(e)}"

# --- LangChain Agent ---
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, input_key="input", output_key="output")


agent = initialize_agent(
    tools=[move_issue_sprint_backlog, get_sprint_issues_by_status, get_active_sprint, get_backlog_issues, close_issue, create_issue, get_issue_status, close_issue, update_issue_status, summarize_issue, summarize_last_reported_issue],
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    memory=memory,
    verbose=True
)

# --- Streamlit Chatbot UI ---
import streamlit as st
import time

# Function to create typing effect
def type_effect(placeholder, text, speed=0.05):
    displayed_text = ""
    for char in text:
        displayed_text += char
        placeholder.markdown(displayed_text)
        time.sleep(speed)  # Adjust speed for typing effect

# Streamlit UI
st.title("Jira Chatbot 🤖")
st.write("Chat with your Jira Assistant!")

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# User input
user_input = st.text_input("Type your message...", key="user_input")

if st.button("Send") and user_input:
    # Store user message
    st.session_state.chat_history.append(("user", user_input))

    # Placeholder for bot response
    bot_message_placeholder = st.empty()

    # Show spinner while waiting for response
    with st.spinner("🤖 Thinking..."):
        response = agent.run(user_input)  # Replace with actual response

    # Apply typing effect once the response is ready
    type_effect(bot_message_placeholder, response, speed=0.05)

    # Update chat history with bot response
    st.session_state.chat_history.append(("bot", response))

# Display chat history
for sender, message in st.session_state.chat_history:
    role = "User" if sender == "user" else "bot"
    with st.chat_message(sender):
        st.markdown(f"<p style='margin: 2px 0; padding: 5px; font-size:14px;'>{message}</p>", unsafe_allow_html=True)

# Clear chat button
if st.button("🗑 Clear Chat"):
    st.session_state.chat_history = []
    st.rerun()
