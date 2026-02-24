import streamlit as st

def inject_custom_css():
    st.markdown("""
        <style>
        /* Import Inter Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* Global Font & Base Text Colors */
        html, body, [class*="css"]  {
            font-family: 'Inter', sans-serif !important;
            color: #F8FAFC !important; /* Extremely light slate for primary text */
        }
        
        /* Force Markdown text to be light */
        .stMarkdown p, .stMarkdown div {
            color: #E2E8F0 !important;
        }

        /* App Background - Deep Dark Slate */
        .stApp {
            background-color: #0B1120 !important;
        }
        
        /* Ensure the main container also gets dark background */
        [data-testid="stAppViewContainer"] {
            background-color: #0B1120 !important;
        }
        [data-testid="stHeader"] {
            background-color: #0B1120 !important;
        }

        /* Sidebar Styling - Slightly lighter dark */
        [data-testid="stSidebar"] {
            background-color: #0F172A !important;
            border-right: 1px solid #1E293B !important;
        }
        [data-testid="stSidebar"] hr {
            border-color: #1E293B !important;
        }

        /* Standardize Cards using st.container(border=True) */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 12px !important;
            border: 1px solid #334155 !important;
            background-color: #1E293B !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5), 0 2px 4px -1px rgba(0, 0, 0, 0.3) !important;
            padding: 1rem !important;
        }

        /* Buttons Styling */
        .stButton>button {
            border-radius: 8px !important;
            font-weight: 500 !important;
            transition: all 0.2s ease-in-out !important;
            border: 1px solid #334155 !important;
            background-color: #1E293B !important;
            color: #F8FAFC !important;
        }
        .stButton>button:hover {
            border-color: #475569 !important;
            background-color: #334155 !important;
        }
        
        /* Primary Buttons */
        .stButton>button[kind="primary"] {
            background-color: #3B82F6 !important; /* Vibrant blue accent for primary actions */
            color: #FFFFFF !important;
            border: none !important;
            box-shadow: 0 0 10px rgba(59, 130, 246, 0.3) !important;
        }
        .stButton>button[kind="primary"]:hover {
            background-color: #2563EB !important;
            box-shadow: 0 0 15px rgba(59, 130, 246, 0.5) !important;
        }
        .stButton>button[kind="primary"] * {
            color: #FFFFFF !important;
        }

        /* Form Text Inputs & Selectboxes */
        div[data-baseweb="input"] > div, 
        div[data-baseweb="select"] > div {
            border-radius: 8px !important;
            border: 1px solid #334155 !important; 
            background-color: #0B1120 !important; /* Pure dark for input background */
            transition: border 0.3s ease !important;
        }
        
        div[data-baseweb="input"] > div:hover, 
        div[data-baseweb="select"] > div:hover {
            border: 1px solid #475569 !important;
        }
        
        /* Focus state for inputs */
        div[data-baseweb="input"] > div.st-focused, 
        div[data-baseweb="select"] > div.st-focused {
            border: 1px solid #3B82F6 !important;
            box-shadow: 0 0 0 1px #3B82F6 !important;
        }
        
        /* Make user input text light inside the fields */
        div[data-baseweb="input"] input, 
        div[data-baseweb="select"] div {
            color: #F8FAFC !important; 
        }
        
        /* Placeholder text color */
        ::placeholder {
            color: #64748B !important;
            opacity: 1 !important;
        }
        
        /* Ensure input labels are visible in dark mode */
        .stTextInput label, .stSelectbox label {
            color: #CBD5E1 !important;
            font-weight: 500 !important;
        }
        
        /* Dropdown options background */
        ul[data-baseweb="menu"] {
            background-color: #1E293B !important;
            border: 1px solid #334155 !important;
        }
        ul[data-baseweb="menu"] li {
            color: #F8FAFC !important;
        }
        ul[data-baseweb="menu"] li:hover {
            background-color: #334155 !important;
        }
        
        /* Form outlines */
        [data-testid="stForm"] {
            border: 1px solid #1E293B !important;
            border-radius: 12px !important;
            padding: 1.5rem !important;
            background-color: #0F172A !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3) !important;
        }

        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            color: #F8FAFC !important;
            font-weight: 600 !important;
            font-family: 'Inter', sans-serif !important;
        }
        
        /* Login Title fix */
        [data-testid="stHeadingWithActionElements"] h1 {
            color: #F8FAFC !important;
            text-shadow: 0 2px 4px rgba(0,0,0,0.5);
        }

        /* Metrics */
        [data-testid="stMetricValue"] {
            font-size: 2rem !important;
            font-weight: 700 !important;
            color: #F8FAFC !important;
        }
        [data-testid="stMetricLabel"] {
            color: #94A3B8 !important;
            font-weight: 500 !important;
        }
        [data-testid="stMetricDelta"] {
            color: #34D399 !important; /* Emerald green for positive metrics if any */
        }
        
        /* Dataframes & Tables */
        [data-testid="stDataFrame"] {
            border: 1px solid #334155 !important;
            border-radius: 8px !important;
            background-color: #0F172A !important;
        }
        [data-testid="stDataFrame"] table {
            color: #E2E8F0 !important;
        }
        [data-testid="stDataFrame"] th {
            background-color: #1E293B !important;
            color: #F8FAFC !important;
            border-bottom: 1px solid #334155 !important;
        }
        [data-testid="stDataFrame"] td {
            border-bottom: 1px solid #1E293B !important;
        }
        
        /* Tabs Styling */
        [data-baseweb="tab"] {
            color: #94A3B8 !important;
            background-color: transparent !important;
        }
        [data-baseweb="tab"][aria-selected="true"] {
            color: #3B82F6 !important;
            border-bottom-color: #3B82F6 !important;
        }
        
        /* Expanders */
        [data-testid="stExpander"] {
            background-color: #1E293B !important;
            border: 1px solid #334155 !important;
            border-radius: 8px !important;
        }
        [data-testid="stExpander"] summary {
            color: #F8FAFC !important;
        }
        
        /* Custom Info/Success/Warning/Error boxes */
        [data-testid="stAlert"] {
            background-color: #1E293B !important;
            border: 1px solid #334155 !important;
            color: #E2E8F0 !important;
        }
        </style>
    """, unsafe_allow_html=True)
