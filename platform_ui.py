 
import os
import streamlit as st
import requests
from langchain_core.messages import AIMessage, HumanMessage
from openai import OpenAI
from dotenv import load_dotenv
# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai_client = OpenAI(api_key=OPENAI_API_KEY)
# Set page configurations and styles
st.set_page_config(page_title="Channels Knowledgebase", page_icon="🧠")
st.title("Channels Knowledgebase")
# Custom CSS styling for the application
st.markdown("""
    <style>
    body {
        background-color: #F4F4F9;
    }
    .css-1lcbmhc {
        background: linear-gradient(to right, #0F2027, #2C5364);
        color: #F4F4F9;
    }
    .stButton button {
        background-color: #ff7e67;
        border-radius: 8px;
        border: none;
        color: white;
        padding: 10px 24px;
        font-size: 16px;
    }
    .stButton button:hover {
        background-color: #db4a39;
    }
    .css-1inwz65 {
        padding: 20px;
        background: #ffffff;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .css-vcb0m8 {
        margin-top: 20px;
    }
    .stTextInput, .stTextInput input {
        padding: 10px;
        border-radius: 8px;
    }
    .stRadio label {
        font-size: 14px;
    }
    .stTextInput input:focus {
        border: 1px solid #007bff;
    }
    </style>
    """, unsafe_allow_html=True)
# Hide the Streamlit menu and footer using custom CSS
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
# Define function to get response from the local server
def get_response(user_query):
    response = requests.post('http://localhost:5000/query', json={"query": user_query})
    if response.status_code == 200:
        relevant_doc_content = response.json().get('response', "No answer from server.")
    else:
        relevant_doc_content = "No relevant information found"
    template = f"""
    You are a helpful assistant. Answer the user's question based strictly on the relevant information retrieved from the database. 
    {f"Relevant Document Information: {relevant_doc_content}" if relevant_doc_content else "No relevant document information was found for this query."}
    User question: {user_query}
    Instructions:
    - If relevant document information is provided, use it to answer the user's question.
    - If no relevant document information is available, respond by stating that there is no relevant information to answer the question at the moment.
    """
    return openai_client.chat.completions.create(
        model="gpt-4o-mini", 
        messages=[{"role": "user", "content": template}],
        max_tokens=500,
        stream=True
    )
# Handle user login state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
# Sidebar with logout button and user details
if st.session_state.logged_in:
    with st.sidebar:
        st.header("👤 User Panel")
        st.markdown(f"**Username:** {st.session_state.get('username', 'Guest')}")
        if st.button("Logout", key="logout_button"):
            st.session_state.logged_in = False
            st.session_state.chat_history = []
            st.rerun()
# If the user is not logged in, show login/registration interface
if not st.session_state.logged_in:
    st.subheader("🔑 Login or Register")
    choice = st.radio("Choose an option:", ['Login', 'Signup'], index=0, horizontal=True)
    # Username and password input fields with placeholder text
    username = st.text_input("Username", placeholder="Enter your username")
    password = st.text_input("Password", type='password', placeholder="Enter your password")
    # Registration logic
    if choice == 'Signup':
        if st.button("Register", key="register_button"):
            if username and password:
                response = requests.post('http://localhost:5000/register', json={"username": username, "password": password})
                if response.status_code == 201:
                    st.success("Registration successful! Please login.")
                elif response.status_code == 400:
                    st.error(response.json().get("error"))
                else:
                    st.error("Error registering the user")
            else:
                st.error("Please provide a username and password")
    # Login logic
    if choice == 'Login':
        if st.button("Login", key="login_button"):
            if username and password:
                response = requests.post('http://localhost:5000/login', json={"username": username, "password": password})
                if response.status_code == 200:
                    st.session_state.logged_in = True
                    st.session_state.username = username  # Store username in session state
                    st.success("Login successful!")
                    st.rerun() 
                else:
                    st.error("Invalid credentials")
            else:
                st.error("Please provide a username and password")
# If the user is logged in, show the chat interface
if st.session_state.logged_in:
    st.subheader("Query the Documents (Chat Interface)")
 
    # Set up chat history in session state if not already
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [AIMessage(content="Hello, how can I help you?")]
 
    # Display conversation history
    for message in st.session_state.chat_history:
        with st.chat_message("AI" if isinstance(message, AIMessage) else "Human"):
            st.write(message.content)
 
    # Handle user input for new queries
    user_query = st.chat_input("Type your message here...")
   
    if user_query is not None and user_query != "":
        # Append the user query to chat history
        st.session_state.chat_history.append(HumanMessage(content=user_query))
       
        with st.chat_message("Human"):
            st.markdown(user_query)
       
 
        with st.chat_message("AI"):
            response = st.write_stream(get_response(user_query))
 
        st.session_state.chat_history.append(AIMessage(content=response))
 