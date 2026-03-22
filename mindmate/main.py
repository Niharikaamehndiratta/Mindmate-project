import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Define project root at module level
project_root = Path(__file__).parent.parent

def setup_paths():
    """Setup project paths only once"""
    # Add both project root and mindmate package to path
    paths_to_add = [
        str(project_root),
        str(project_root.parent),
        str(project_root / 'mindmate'),  # Corrected path to mindmate package
        str(project_root.parent / 'mindmate')
    ]
    # Remove any existing paths to avoid duplicates
    sys.path = [p for p in sys.path if str(project_root) not in p and 
               str(project_root.parent) not in p and
               str(project_root / 'mindmate') not in p and
               str(project_root.parent / 'mindmate') not in p]
    
    for path in paths_to_add:
        if path not in sys.path:
            sys.path.insert(0, path)
    
    # Set PYTHONPATH if not set
    if 'PYTHONPATH' not in os.environ:
        os.environ['PYTHONPATH'] = os.pathsep.join(paths_to_add)
    else:
        existing = os.environ['PYTHONPATH'].split(os.pathsep)
        for path in paths_to_add:
            if path not in existing:
                existing.insert(0, path)
        os.environ['PYTHONPATH'] = os.pathsep.join(existing)
    
    # Debug output with more details
    print("\n=== Path Configuration ===")
    print(f"Python Path: {sys.path}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', '')}")
    print(f"Project Root: {project_root}")
    print(f"Project Parent: {project_root.parent}")
    print(f"Mindmate Path: {project_root / 'mindmate'}")
    print(f"Absolute Paths Exist:")
    print(f"- Project Root: {project_root.exists()}")
    print(f"- Mindmate Dir: {(project_root / 'mindmate').exists()}")
    print("=========================\n")

# Always setup paths, not just when run directly
setup_paths()

# Load environment variables from .env file first
env_path = os.path.join(project_root, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

import os
import sys
import streamlit as st
from mindmate.utils.auth import show_login_form, show_signup_form
from mindmate.pages.therapist_auth import show as show_therapist_auth
from mindmate.pages.therapist_dashboard import show_dashboard
from mindmate.pages import (
    home,
    journal,
    mood_tracker,
    goals,
    professional_help,
    chatbot,
    meditation_tracker,
    sleep_tracker,
    community,
    wellness_dashboard,
    productivity_timer,
    breathing_exercises,
    analytics,
    personality_rpg,
    personalization,
    therapist_patients
)

# Sidebar navigation
PAGES = {
    "Home": home,
    "Personalization": personalization,
    "Journal": journal,
    "Meditation": meditation_tracker,
    "Mood Tracker": mood_tracker,
    "Sleep Tracker": sleep_tracker,
    "Wellness Goals": goals,
    "Find Therapist": professional_help,
    "Community": community,
    "Chatbot": chatbot,
    "Analytics": analytics,
    "Wellness Dashboard": wellness_dashboard,
    "Productivity Timer": productivity_timer,
    "Breathing Exercises": breathing_exercises,
    "Personality RPG": personality_rpg
}

def main():
    """Main application with authentication flow"""
    st.set_page_config(page_title="MindMate", layout="wide")

    if 'user' not in st.session_state:
        st.session_state.user = None

    # Show login/signup if not authenticated
    if not st.session_state.get('user') and not st.session_state.get('therapist_logged_in'):
        tab1, tab2, tab3 = st.tabs(["User Login", "User Sign Up", "Therapist Portal"])
        with tab1:
            user = show_login_form()
            if user:
                st.session_state.user = user
                st.session_state.user_type = 'user'
                st.rerun()
        with tab2:
            if show_signup_form():
                st.rerun()
        with tab3:
            show_therapist_auth()
        return

    # Main app for authenticated users
    if st.session_state.get('therapist_logged_in'):
        st.sidebar.title(f"Dr. {st.session_state.therapist_email.split('@')[0]}")
    elif st.session_state.user:
        user_name = st.session_state.user.get('first_name', 'User')
        st.sidebar.title(f"Welcome, {user_name}!")
    
    if st.sidebar.button("Logout"):
        if st.session_state.get('therapist_logged_in'):
            st.session_state.clear()
        else:
            st.session_state.user = None
        st.rerun()
    
    # Navigation and page display
    if st.session_state.get('therapist_logged_in'):
        st.sidebar.markdown("Therapist Dashboard")
        selection = st.sidebar.radio("Navigation", ["Dashboard", "Patients"])
        if selection == "Dashboard":
            show_dashboard()
            return
        elif selection == "Patients":
            therapist_patients.show()
            return
    else:
        st.sidebar.markdown("Your mental wellness companion")
        selection = st.sidebar.radio("Navigation", list(PAGES.keys()))
        page = PAGES[selection]
    
    try:
        # Standardize page function calls
        if hasattr(page, 'show'):
            # Safely get user ID with fallback
            user_id = st.session_state.user.get('id') if st.session_state.user else None
            if user_id:
                page.show(user_id)
            else:
                st.error("User session not found. Please log in again.")
                st.session_state.user = None
                st.rerun()
        else:
            raise AttributeError(f"Page {selection} has no show() function")
    except Exception as e:
        st.error(f"Error loading {selection}: {str(e)}")

if __name__ == "__main__":
    main()
