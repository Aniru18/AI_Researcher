# import streamlit as st
# from ai_researcher import INITIAL_PROMPT, graph, config
# from pathlib import Path
# import logging
# from langchain_core.messages import AIMessage

# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Basic app config
# st.set_page_config(page_title="Research AI Agent", page_icon="📄")
# st.title("📄 Research AI Agent")

# # Initialize session state
# if "chat_history" not in st.session_state:
#     st.session_state.chat_history = []
#     logger.info("Initialized chat history")

# if "pdf_path" not in st.session_state:
#     st.session_state.pdf_path = None

# # Chat interface
# user_input = st.chat_input("What research topic would you like to explore?")

# if user_input:
#     # Log and display user input
#     logger.info(f"User input: {user_input}")
#     st.session_state.chat_history.append({"role": "user", "content": user_input})
#     st.chat_message("user").write(user_input)

#     # Prepare input for the agent
#     chat_input = {"messages": [{"role": "system", "content": INITIAL_PROMPT}] + st.session_state.chat_history}
#     logger.info("Starting agent processing...")

#     # Stream agent response
#     full_response = ""
#     for s in graph.stream(chat_input, config, stream_mode="values"):
#         message = s["messages"][-1]
        
#         # Handle tool calls (log only)
#         if getattr(message, "tool_calls", None):
#             for tool_call in message.tool_calls:
#                 logger.info(f"Tool call: {tool_call['name']}")
        
#         # Handle assistant response
#         if isinstance(message, AIMessage) and message.content:
#             text_content = message.content if isinstance(message.content, str) else str(message.content) 
#             full_response += text_content + " "
#             st.chat_message("assistant").write(full_response)
            

#     # Add final response to history
#     if full_response:
#         st.session_state.chat_history.append({"role": "assistant", "content": full_response})


import streamlit as st
import logging
import re
from pathlib import Path
from typing import Optional

from pydantic import BaseModel
from langchain_core.messages import AIMessage

from ai_researcher import INITIAL_PROMPT, graph, config


# ===============================
# Logging setup
# ===============================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ===============================
# Streamlit App Config
# ===============================
st.set_page_config(
    page_title="Research AI Agent",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Research AI Agent")


# ===============================
# Pydantic Response Schema
# ===============================
class AgentResponse(BaseModel):
    text: str
    status: Optional[str] = None
    pdf_path: Optional[str] = None


# ===============================
# Gemini → Pydantic Normalizer
# ===============================
def parse_agent_message(message: AIMessage) -> AgentResponse:
    """
    Normalize Gemini / LangChain message into a structured AgentResponse
    """
    content = message.content
    text = ""

    # Gemini structured content
    if isinstance(content, list):
        text = "".join(
            part.get("text", "")
            for part in content
            if part.get("type") == "text"
        )

    # Normal string content
    elif isinstance(content, str):
        text = content

    text = text.strip()

    # Detect PDF path (Windows-friendly)
    pdf_path = None
    match = re.search(r"[A-Z]:\\.*?\.pdf", text)
    if match:
        pdf_path = match.group(0)

    # Detect simple status
    status = None
    lowered = text.lower()
    if "re-render" in lowered or "regenerate" in lowered:
        status = "rerendering_pdf"
    elif pdf_path:
        status = "pdf_generated"

    return AgentResponse(
        text=text,
        status=status,
        pdf_path=pdf_path
    )


# ===============================
# Session State Init
# ===============================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    logger.info("Chat history initialized")

if "pdf_path" not in st.session_state:
    st.session_state.pdf_path = None


# ===============================
# Chat Input
# ===============================
user_input = st.chat_input("What research topic would you like to explore?")


# ===============================
# Main Chat Flow
# ===============================
if user_input:
    logger.info(f"User input: {user_input}")

    # Store user message
    st.session_state.chat_history.append(
        {"role": "user", "content": user_input}
    )

    st.chat_message("user").write(user_input)

    # Prepare agent input
    chat_input = {
        "messages": [
            {"role": "system", "content": INITIAL_PROMPT}
        ] + st.session_state.chat_history
    }

    logger.info("Starting agent stream")

    # Assistant UI placeholder (smooth streaming)
    assistant_placeholder = st.chat_message("assistant").empty()
    full_response_text = ""

    # Stream agent output
    for s in graph.stream(chat_input, config, stream_mode="values"):
        message = s["messages"][-1]

        # Log tool calls only (no UI spam)
        if getattr(message, "tool_calls", None):
            for tool_call in message.tool_calls:
                logger.info(f"Tool called: {tool_call['name']}")

        # Handle assistant messages
        if isinstance(message, AIMessage) and message.content:
            response = parse_agent_message(message)

            if response.text:
                full_response_text += response.text + "\n\n"
                assistant_placeholder.write(full_response_text)

            # Handle PDF output
            if response.pdf_path:
                st.session_state.pdf_path = response.pdf_path

    # Persist assistant response
    if full_response_text.strip():
        st.session_state.chat_history.append(
            {"role": "assistant", "content": full_response_text.strip()}
        )


# ===============================
# PDF Download Section
# ===============================
if st.session_state.pdf_path:
    pdf_file = Path(st.session_state.pdf_path)

    if pdf_file.exists():
        st.divider()
        st.success("📄 Research paper generated successfully")

        with open(pdf_file, "rb") as f:
            st.download_button(
                label="⬇️ Download PDF",
                data=f,
                file_name=pdf_file.name,
                mime="application/pdf"
            )
