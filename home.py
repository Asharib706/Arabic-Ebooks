import streamlit as st
from streamlit_extras.switch_page_button import switch_page

# Page configuration - no sidebar
st.set_page_config(
    page_title="Arabic Ebook Portal",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="collapsed"  # This hides the sidebar
)

# Custom CSS to hide sidebar and style navigation
st.markdown("""
<style>
    /* Hide the sidebar completely */
    section[data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* Main header style */
    .header {
        font-size: 2.5em;
        color: #2c3e50;
        text-align: center;
        margin: 20px 0 40px 0;
    }
    
    /* App card styling */
    .app-card {
        border-radius: 15px;
        padding: 30px;
        margin: 25px auto;
        max-width: 500px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        background: white;
        border: 1px solid #e0e0e0;
    }
    
    .app-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.15);
    }
    
    .app-title {
        font-size: 1.8em;
        color: #2c3e50;
        margin-bottom: 15px;
        text-align: center;
    }
    
    .app-description {
        color: #666;
        margin-bottom: 25px;
        text-align: center;
        line-height: 1.6;
    }
    
    /* Button styling */
    .nav-btn {
        width: 100%;
        padding: 12px;
        font-size: 1.1em;
        border-radius: 8px;
        margin-top: 15px;
    }
    
    /* Footer styling */
    .footer {
        text-align: center;
        margin-top: 50px;
        color: #95a5a6;
        padding: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="header">Arabic Ebook Portal</div>', unsafe_allow_html=True)

# App Navigation Cards
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="app-card">
        <div class="app-title">Arabic PDF Processing</div>
        <div class="app-description">
            Convert Arabic PDFs to text, extract chapters,etc. with advanced processing features.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Go to Ebook Reader", key="reader_btn"):
        switch_page("PDF_Processing")

with col2:
    st.markdown("""
    <div class="app-card">
        <div class="app-title">🔧 Ebook Tools</div>
        <div class="app-description">
            Read Arabic ebooks with chapter navigation ,Docx file Conversion and text-to-speech functionality
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Go to Ebook Tools", key="tools_btn"):
        switch_page("Ebooks.py")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #95a5a6;">
    <p>Developed by Muhammad Asharib • v1.0</p>
</div>
""", unsafe_allow_html=True)