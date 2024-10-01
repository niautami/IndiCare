import streamlit as st
import requests
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
import time

load_dotenv()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.set_page_config(page_title="IndiCareBot", page_icon="👩‍⚕️")


# Check if chat history is empty and add a welcome message
if not st.session_state.chat_history:
    welcome_message = AIMessage("Hello! I'm here to answer questions specifically about Aboriginal perinatal mental health and cultural competence. Feel free to ask me anything in this area!")
    st.session_state.chat_history.append(welcome_message)

# Create a sticky header using sidebar
st.sidebar.title("👩‍⚕️ IndiCareBot")
st.title("IndiCareBot")

# Predefined sample questions
sample_questions = [
    "What if an Aboriginal who is willing to be suicidal makes me promise not to tell anyone else?",
    "What words should I avoid when talking to an Aboriginal woman?",
    "How can I talk to an Aboriginal mother who I think is depressed?",
    "What should I say to an Aboriginal woman who has a stillborn baby?",
]

# Function to make API call to Flask server
def get_response_from_api(query, chat_history):
    api_url = "https://3d72-134-115-64-42.ngrok-free.app/get_response"  # Replace with your Flask server URL
    data = {
        "query": query,
        "chat_history": [msg.content for msg in chat_history if isinstance(msg, HumanMessage)]
    }
    try:
        response = requests.post(api_url, json=data)
        if response.status_code == 200:
            return response.json().get("response", "No response received.")
        else:
            return "Error: Failed to get response from server"
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"

# Display sample questions in the sidebar
for question in sample_questions:
    if st.sidebar.button(question, key=question):
        # Only add the question to chat history if it's not already the last message
        if not st.session_state.chat_history or st.session_state.chat_history[-1].content != question:
            st.session_state.chat_history.append(HumanMessage(question))
            
            # Get AI response and display it
            with st.spinner("Thinking..."):
                ai_response = get_response_from_api(question, st.session_state.chat_history)
            st.session_state.chat_history.append(AIMessage(ai_response))

# Conversation
for message in st.session_state.chat_history:
    if isinstance(message, HumanMessage):
        with st.chat_message("Human"):
            st.markdown(message.content)
    else:
        with st.chat_message("AI"):
            st.markdown(message.content)

# Chat input
user_input = st.chat_input("Your question")
if user_input is not None and user_input != "":
    st.session_state.chat_history.append(HumanMessage(user_input))
    
    # Get AI response and display it
    with st.spinner("Thinking..."):
        ai_response = get_response_from_api(user_input, st.session_state.chat_history)
    st.session_state.chat_history.append(AIMessage(ai_response))

    # Force a rerun to update the chat display
    st.experimental_rerun()