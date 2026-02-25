import streamlit as st

def inject_theme_toggle():
    """Renders a dark/light mode toggle in the sidebar."""
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = True

    # We use a toggle in the sidebar
    st.sidebar.toggle("🌙 Dark Mode", value=st.session_state.dark_mode, key="theme_toggle",
                       on_change=_toggle_theme)

    # Inject JS to set a class on the root HTML element
    theme_class = "theme-dark" if st.session_state.dark_mode else "theme-light"
    st.markdown(f"""
        <script>
            document.documentElement.className = '{theme_class}';
        </script>
    """, unsafe_allow_html=True)

def _toggle_theme():
    st.session_state.dark_mode = st.session_state.theme_toggle

def inject_custom_css():
    st.markdown("""
        <style>
        /* Import Inter Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* ── THEME VARIABLES ── */
        :root, .theme-dark {
            --bg-page: #0B1120;
            --bg-sidebar: #0F172A;
            --bg-card: #1E293B;
            --bg-input: #0B1120;
            --border: #334155;
            --border-hover: #475569;
            --text-main: #F8FAFC;
            --text-muted: #94A3B8;
            --text-md: #E2E8F0;
            --accent: #3B82F6;
            --accent-hover: #2563EB;
            --success: #34D399;
        }

        .theme-light {
            --bg-page: #F8FAFC;
            --bg-sidebar: #FFFFFF;
            --bg-card: #FFFFFF;
            --bg-input: #FFFFFF;
            --border: #E2E8F0;
            --border-hover: #CBD5E1;
            --text-main: #0F172A;
            --text-muted: #64748B;
            --text-md: #334155;
            --accent: #2563EB;
            --accent-hover: #1D4ED8;
            --success: #059669;
        }

        /* Global Font & Base Text Colors */
        html, body, [class*="css"]  {
            font-family: 'Inter', sans-serif !important;
            color: var(--text-main) !important;
        }
        
        /* Force Markdown text */
        .stMarkdown p, .stMarkdown div {
            color: var(--text-md) !important;
        }

        /* App Background */
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background-color: var(--bg-page) !important;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: var(--bg-sidebar) !important;
            border-right: 1px solid var(--border) !important;
        }
        [data-testid="stSidebar"] hr { border-color: var(--border) !important; }

        /* Standardize Cards using st.container(border=True) */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 12px !important;
            border: 1px solid var(--border) !important;
            background-color: var(--bg-card) !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.05) !important;
            padding: 1rem !important;
        }

        /* Buttons Styling */
        .stButton>button {
            border-radius: 8px !important;
            font-weight: 500 !important;
            transition: all 0.2s ease-in-out !important;
            border: 1px solid var(--border) !important;
            background-color: var(--bg-card) !important;
            color: var(--text-main) !important;
        }
        .stButton>button:hover {
            border-color: var(--border-hover) !important;
            background-color: var(--bg-sidebar) !important;
        }
        
        /* Primary Buttons */
        .stButton>button[kind="primary"] {
            background-color: var(--accent) !important;
            color: #FFFFFF !important;
            border: none !important;
            box-shadow: 0 0 10px rgba(59, 130, 246, 0.2) !important;
        }
        .stButton>button[kind="primary"]:hover {
            background-color: var(--accent-hover) !important;
            box-shadow: 0 0 15px rgba(59, 130, 246, 0.4) !important;
        }
        .stButton>button[kind="primary"] * {
            color: #FFFFFF !important;
        }

        /* Form Text Inputs & Selectboxes */
        div[data-baseweb="input"] > div, 
        div[data-baseweb="select"] > div {
            border-radius: 8px !important;
            border: 1px solid var(--border) !important; 
            background-color: var(--bg-input) !important;
            transition: border 0.3s ease !important;
        }
        
        div[data-baseweb="input"] > div:hover, 
        div[data-baseweb="select"] > div:hover {
            border: 1px solid var(--border-hover) !important;
        }
        
        /* Focus state for inputs */
        div[data-baseweb="input"] > div.st-focused, 
        div[data-baseweb="select"] > div.st-focused {
            border: 1px solid var(--accent) !important;
            box-shadow: 0 0 0 1px var(--accent) !important;
        }
        
        div[data-baseweb="input"] input, 
        div[data-baseweb="select"] div {
            color: var(--text-main) !important; 
        }
        
        ::placeholder {
            color: var(--text-muted) !important;
            opacity: 1 !important;
        }
        
        .stTextInput label, .stSelectbox label {
            color: var(--text-main) !important;
            font-weight: 500 !important;
        }
        
        /* Dropdown options background */
        ul[data-baseweb="menu"] {
            background-color: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
        }
        ul[data-baseweb="menu"] li {
            color: var(--text-main) !important;
        }
        ul[data-baseweb="menu"] li:hover {
            background-color: var(--bg-sidebar) !important;
        }
        
        /* Form outlines */
        [data-testid="stForm"] {
            border: 1px solid var(--border) !important;
            border-radius: 12px !important;
            padding: 1.5rem !important;
            background-color: var(--bg-card) !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
        }

        /* Headers */
        h1, h2, h3, h4, h5, h6, [data-testid="stHeadingWithActionElements"] h1 {
            color: var(--text-main) !important;
            font-weight: 600 !important;
            font-family: 'Inter', sans-serif !important;
        }

        /* Metrics */
        [data-testid="stMetricValue"] {
            font-size: 2rem !important;
            font-weight: 700 !important;
            color: var(--text-main) !important;
        }
        [data-testid="stMetricLabel"] {
            color: var(--text-muted) !important;
            font-weight: 500 !important;
        }
        [data-testid="stMetricDelta"] {
            color: var(--success) !important;
        }
        
        /* Dataframes & Tables */
        [data-testid="stDataFrame"] {
            border: 1px solid var(--border) !important;
            border-radius: 8px !important;
            background-color: var(--bg-card) !important;
        }
        [data-testid="stDataFrame"] table {
            color: var(--text-md) !important;
        }
        [data-testid="stDataFrame"] th {
            background-color: var(--bg-card) !important;
            color: var(--text-main) !important;
            border-bottom: 1px solid var(--border) !important;
        }
        [data-testid="stDataFrame"] td {
            border-bottom: 1px solid var(--border) !important;
        }
        
        /* Tabs Styling */
        [data-baseweb="tab"] {
            color: var(--text-muted) !important;
            background-color: transparent !important;
        }
        [data-baseweb="tab"][aria-selected="true"] {
            color: var(--accent) !important;
            border-bottom-color: var(--accent) !important;
        }
        
        /* Expanders */
        [data-testid="stExpander"] {
            background-color: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px !important;
        }
        [data-testid="stExpander"] summary {
            color: var(--text-main) !important;
        }
        
        /* Alerts */
        [data-testid="stAlert"] {
            background-color: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
            color: var(--text-md) !important;
        }
        </style>
    """, unsafe_allow_html=True)
