import streamlit as st
import os
import json
import base64
from dotenv import load_dotenv
from tavily import TavilyClient
import google.generativeai as genai

# --- 1. SETUP & THEME ---
load_dotenv()
st.set_page_config(page_title="MedLink Community Hub", page_icon="🩺", layout="wide")

# Helper function to convert local image to Base64
def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# File path check
wallpaper_filename = "bg.jpg" 

if os.path.exists(wallpaper_filename):
    try:
        bin_str = get_base64(wallpaper_filename)
        # --- CSS BLOCK (Properly Indented) ---
        st.markdown(f"""
            <style>
            .stApp {{
                /* BLACK tint at 70% opacity (0.7) for better contrast */
                background: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), 
                            url("data:image/png;base64,{bin_str}");
                background-size: cover;
                background-attachment: fixed;
            }}
            
            /* Global Text Color: White */
            [data-testid="stHeader"], .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp span, .stApp li {{
                color: white !important;
            }}

            /* Input box styling */
            .stChatInput textarea {{
                color: white !important;
                background-color: rgba(255, 255, 255, 0.1) !important;
            }}

            /* Glassmorphism Post Cards */
            .post-card {{
                background: rgba(255, 255, 255, 0.1); 
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.2);
                padding: 25px;
                border-radius: 15px;
                margin-bottom: 25px;
                color: white !important;
            }}
            
            .post-card h3 {{
                color: #00d4ff !important; 
                margin-bottom: 10px;
            }}
            </style>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.sidebar.error(f"Error loading image: {e}")
else:
    st.sidebar.warning(f"File '{wallpaper_filename}' not found in {os.getcwd()}")

# Initialize Session State
if "last_ai_response" not in st.session_state:
    st.session_state.last_ai_response = None

# Initialize AI Tools
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash") 

# --- 2. DATABASE LOGIC ---
DB_FILE = "community_posts.json"

def load_posts():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: return []
    return []

def save_post(username, content):
    posts = load_posts()
    posts.insert(0, {"user": username, "content": content})
    with open(DB_FILE, "w") as f: 
        json.dump(posts, f, indent=4)

# --- 3. UI NAVIGATION ---
st.sidebar.title("🩺 MedLink Hub")
mode = st.sidebar.radio("Navigation", ["AI Research Lab", "Community Wall"])

if mode == "AI Research Lab":
    st.title("🔬 AI Medical Assistant")
    query = st.chat_input("Ex: Compare symptoms of Influenza vs COVID-19")

    if query:
        with st.spinner("Searching medical databases..."):
            search_result = tavily.search(query=query, search_depth="advanced")
            prompt = f"""
            Search Context: {search_result}
            User Question: {query}
            Instruction: Provide a professional medical summary. 
            - Use a MARKDOWN TABLE for comparisons.
            - Cite sources clearly.
            """
            response = model.generate_content(prompt)
            st.session_state.last_ai_response = response.text

    if st.session_state.last_ai_response:
        st.markdown(st.session_state.last_ai_response)
        if st.button("📌 Share to Community Wall"):
            save_post("Student_Researcher", st.session_state.last_ai_response)
            st.success("Shared successfully!")
            st.rerun() # Refresh to update the wall data

elif mode == "Community Wall":
    st.title("🤝 Shared Medical Insights")
    posts = load_posts()
    
    if not posts:
        st.info("The wall is empty. Ask the AI something first!")
    
    for p in posts:
        st.markdown(f"""
        <div class="post-card">
            <h3>👤 {p['user']}</h3>
            <div>{p['content']}</div>
        </div>
        """, unsafe_allow_html=True)