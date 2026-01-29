CUSTOM_CSS = """
<style>
    /* Global App Background */
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgb(0, 0, 0) 0%, rgb(30, 30, 30) 90.2%);
        color: #ffffff;
        font-family: 'Inter', sans-serif;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #00e5ff !important;
        font-weight: 700;
        text-shadow: 0px 0px 10px rgba(0, 229, 255, 0.4);
    }

    /* Cards/Containers (Glassmorphism) */
    .stContainer, .stForm {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    /* Inputs */
    .stTextInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.1);
        color: white;
        border: 1px solid #333;
        border-radius: 10px;
    }
    .stTextInput > div > div > input:focus {
        border-color: #00e5ff;
        box-shadow: 0 0 10px rgba(0, 229, 255, 0.2);
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 114, 255, 0.3);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 114, 255, 0.5);
    }
    .stButton > button:active {
        transform: translateY(1px);
    }

    /* Chat Bubbles */
    .chat-bubble {
        padding: 10px 15px;
        border-radius: 15px;
        margin-bottom: 10px;
        max-width: 80%;
        width: fit-content;
        position: relative;
    }
    
    .role-user {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-bottom-right-radius: 2px;
        margin-left: auto;
    }
    
    .role-other {
        background: rgba(255, 255, 255, 0.1);
        color: #e0e0e0;
        border-bottom-left-radius: 2px;
        margin-right: auto;
    }

    /* Info Box */
    .stAlert {
        border-radius: 10px;
        background-color: rgba(0, 150, 255, 0.1);
        border: 1px solid rgba(0, 150, 255, 0.3);
    }
</style>
"""
