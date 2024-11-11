import streamlit as st
import hashlib
import sqlite3
from datetime import datetime
import time
import requests
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database functions
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, created_date TEXT)''')
    conn.commit()
    conn.close()

def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_login(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT password FROM users WHERE username=?', (username,))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0] == make_hash(password)
    return False

def sign_up(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users VALUES (?, ?, ?)', 
                 (username, make_hash(password), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# Chat functions
def get_response_from_api(query, chat_history):
    api_url = "https://3d72-134-115-64-42.ngrok-free.app/get_response"
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

def main():
    # Page configuration
    st.set_page_config(page_title="IndiCareBot", page_icon="👩‍⚕️")
    
    # Initialize database
    init_db()
    
    # Initialize session states
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'current_tab' not in st.session_state:
        st.session_state.current_tab = 0

    # Login/Signup Section
    if not st.session_state.logged_in:
        st.title("Welcome to IndiCareBot")
        
        # Create tabs
        login_tab, signup_tab = st.tabs(["Login", "Sign Up"])
        
        # Login tab
        with login_tab:
            st.header("Login")
            login_username = st.text_input("Username", key="login_username")
            login_password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login"):
                if check_login(login_username, login_password):
                    st.session_state.logged_in = True
                    st.session_state.username = login_username
                    # Initialize chat history with welcome message
                    welcome_message = AIMessage("Hello! I'm here to answer questions specifically about Aboriginal perinatal mental health and cultural competence. Feel free to ask me anything in this area!")
                    st.session_state.chat_history = [welcome_message]
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        # Sign Up tab
        with signup_tab:
            st.header("Sign Up")
            new_username = st.text_input("Username", key="new_username")
            new_password = st.text_input("Password", type="password", key="new_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
            
            if st.button("Sign Up"):
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters long")
                else:
                    if sign_up(new_username, new_password):
                        placeholder = st.empty()
                        placeholder.success("Account created successfully! Redirecting to login...")
                        time.sleep(1)
                        st.session_state.current_tab = 0
                        placeholder.empty()
                        st.rerun()
                    else:
                        st.error("Username already exists")
    
    else:
        # Main chat interface
        st.sidebar.title("👩‍⚕️ IndiCareBot")
        st.title("IndiCareBot")

        # Predefined sample questions
        sample_questions = [
            "What if an Aboriginal who is willing to be suicidal makes me promise not to tell anyone else?",
            "What words should I avoid when talking to an Aboriginal woman?",
            "How can I talk to an Aboriginal mother who I think is depressed?",
            "What should I say to an Aboriginal woman who has a stillborn baby?",
        ]

        # Display sample questions in the sidebar
        for question in sample_questions:
            if st.sidebar.button(question, key=question):
                if not st.session_state.chat_history or st.session_state.chat_history[-1].content != question:
                    st.session_state.chat_history.append(HumanMessage(question))
                    with st.spinner("Thinking..."):
                        ai_response = get_response_from_api(question, st.session_state.chat_history)
                    st.session_state.chat_history.append(AIMessage(ai_response))

        # Display chat history
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
            with st.spinner("Thinking..."):
                ai_response = get_response_from_api(user_input, st.session_state.chat_history)
            st.session_state.chat_history.append(AIMessage(ai_response))
            st.experimental_rerun()

        # Logout button in sidebar
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.chat_history = []
            st.rerun()

if __name__ == "__main__":
    main()
