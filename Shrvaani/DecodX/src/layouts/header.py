import streamlit as st
import base64

def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def render_header():
    """
    Renders the professional header and hero section for DecodX.
    """
    # Use the persistent hero logo from artifacts
    logo_path = "/Users/alexander/.gemini/antigravity/brain/5adb2973-6fcb-4f82-b3b8-f58a23d5a713/decodx_hero_logo_1770050462776.png"
    
    try:
        logo_b64 = get_base64_image(logo_path)
        st.markdown(f"""
            <div class="main-header" style="display: flex; align-items: center; justify-content: center; gap: 1rem;">
                <img src="data:image/png;base64,{logo_b64}" style="height: 50px;">
                <span>DecodX</span>
            </div>
        """, unsafe_allow_html=True)
    except:
        st.markdown("""
            <div class="main-header" style="text-align: center;">
                <span>DecodX</span>
            </div>
        """, unsafe_allow_html=True)
        
    st.markdown('<div class="sub-header">Decision Intelligence & Enterprise Governance</div>', unsafe_allow_html=True)

    # Hero Section
    if not st.session_state.get("messages"):
        col_h1, col_h2, col_h3 = st.columns([1, 2, 1])
        with col_h2:
            st.markdown("""
                <div style='text-align: center; background: rgba(255,255,255,0.03); padding: 2rem; border-radius: 1rem; border: 1px solid rgba(255,255,255,0.1); backdrop-filter: blur(10px);'>
                    <h2 style='margin-bottom: 0.5rem;'>Welcome to the Hub</h2>
                    <p style='color: #94a3b8; font-size: 1.1rem;'>Ask me about regional sales trends, policy compliance, or suggest updates to corporate guidelines.</p>
                    <div style='display: flex; gap: 0.5rem; justify-content: center; margin-top: 1.5rem;'>
                        <span class='mcp-badge'>● SECURE STORE ACTIVE</span>
                        <span class='mcp-badge'>● AUDIT LOG ENABLED</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
