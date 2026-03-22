import streamlit as st
import sqlite3
from pathlib import Path
import hashlib
from datetime import datetime
from typing import Optional, Tuple, Dict
from mindmate.utils.animations import (
    render_lottie,
    LOGIN_ANIMATION,
    LOADING_ANIMATION,
    SIGNUP_ANIMATION,
    PARTICLE_BG_ANIMATION
)

# Animation URLs and load function moved to mindmate/utils/animations.py

DB_PATH = Path(__file__).parent.parent / "data" / "mindmate.db"

def get_db_connection():
    """Create and return a database connection"""
    return sqlite3.connect(DB_PATH)

def hash_password(password: str) -> str:
    """Hash a password for storing"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash: str, provided_password: str) -> bool:
    """Verify a stored password against one provided by user"""
    return stored_hash == hash_password(provided_password)

def create_user(username: str, email: str, password: str, 
               first_name: str, last_name: str,
               age: Optional[int] = None, 
               gender: Optional[str] = None) -> bool:
    """Create a new user in the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, first_name, last_name, age, gender)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (username, email, hash_password(password), first_name, last_name, age, gender))
        
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Username or email already exists
    finally:
        conn.close()

def create_admin_user():
    """Create admin user if not exists"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if admin exists
        cursor.execute("SELECT id FROM users WHERE username = 'amaan'")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, first_name, last_name, is_admin)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ('amaan', 'admin@mindmate.com', hash_password('amaan'), 'Admin', 'User', 1))
            conn.commit()
    finally:
        conn.close()

def authenticate_user(username: str, password: str) -> Tuple[bool, Optional[Dict]]:
    """Authenticate a user and return user data if successful"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, email, password_hash, first_name, last_name, age, gender, is_admin
            FROM users WHERE username = ?
        """, (username,))
        
        user = cursor.fetchone()
        if user and verify_password(user[3], password):
            # Update last login time
            cursor.execute("""
                UPDATE users SET last_login = ? WHERE id = ?
            """, (datetime.now(), user[0]))
            conn.commit()
            
            return True, {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'first_name': user[4],
                'last_name': user[5],
                'age': user[6],
                'gender': user[7],
                'is_admin': bool(user[8])
            }
        return False, None
    finally:
        conn.close()

def show_login_form() -> Optional[Dict]:
    """Display login form with animations and return user data if authenticated"""
    # Ensure admin user exists
    create_admin_user()
    
    # Add custom CSS
    st.markdown("""
    <style>
        .login-container {
            max-width: 500px;
            margin: 0 auto;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            background: white;
            animation: fadeIn 1s ease-in-out;
        }
        @keyframes fadeIn {
            from {opacity: 0; transform: translateY(-20px);}
            to {opacity: 1; transform: translateY(0);}
        }
        .login-title {
            font-size: 2.2rem;
            font-weight: 700;
            color: #2e86de;
            margin-bottom: 1.5rem;
            text-align: center;
            animation: slideIn 1s ease forwards;
        }
        @keyframes slideIn {
            from {opacity: 0; transform: translateX(-50px);}
            to {opacity: 1; transform: translateX(0);}
        }
        .stTextInput>div>div>input {
            border-radius: 8px;
            padding: 12px;
            border: 2px solid #e0e0e0;
            transition: all 0.3s ease;
            box-shadow: 0 0 5px rgba(46,134,222,0);
        }
        .stTextInput>div>div>input:focus {
            border-color: #2e86de;
            box-shadow: 0 0 8px rgba(46,134,222,0.6);
            transition: box-shadow 0.3s ease;
        }
        .stButton>button {
            width: 100%;
            padding: 12px;
            border-radius: 8px;
            border: none;
            background: linear-gradient(135deg, #2e86de, #1e6fbf);
            color: white;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 10px rgba(46,134,222,0.3);
        }
        .stButton>button:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(46,134,222,0.5);
        }
        /* Particle background container */
        #particle-background {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            pointer-events: none;
        }
    </style>
    """, unsafe_allow_html=True)

    # Display particle background animation
    # Professional background animation with optimized settings
    render_lottie(
        PARTICLE_BG_ANIMATION,
        height=800,
        key="particle_bg",
        loop=True,
        quality="high",
        speed=0.8
    )

    with st.container():
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Display login animation using new render_lottie helper
            render_lottie(
                LOGIN_ANIMATION,
                height=300,
                key="login",
                loop=True,
                quality="high",
                speed=1.2
            )
        
        with col2:
            st.markdown('<div class="login-title">Welcome Back</div>', unsafe_allow_html=True)
            
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                
                login_button = st.form_submit_button("Login")
                
                if login_button:
                    # Show loading animation during authentication
                    with st.spinner("Authenticating..."):
                        render_lottie(
                            LOADING_ANIMATION,
                            height=150,
                            key="loading",
                            loop=True,
                            quality="high",
                            speed=1.5
                        )
            if username and password:
                authenticated, user = authenticate_user(username, password)
                if authenticated:
                    return user
                st.error("Invalid username or password")
            else:
                st.warning("Please enter both username and password")
    return None


def show_signup_form() -> bool:
    """Display signup form and return True if user created successfully"""
    with st.container():
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Display signup animation using new render_lottie helper
            render_lottie(
                SIGNUP_ANIMATION,
                height=300,
                key="signup",
                loop=True,
                quality="high",
                speed=1.2
            )
            st.markdown('<h2 style="text-align: center; color: #2e86de;">MindMate: Your mental health chatbot</h2>', 
                       unsafe_allow_html=True)
        
        with col2:
            with st.form("signup_form"):
                st.subheader("Create a MindMate Account")
                form_col1, form_col2 = st.columns(2)
                with form_col1:
                    username = st.text_input("Username (required)", placeholder="Choose a username")
                    email = st.text_input("Email (required)", placeholder="Your email")
                    first_name = st.text_input("First Name (required)", placeholder="Your first name")
                    last_name = st.text_input("Last Name (required)", placeholder="Your last name")
                with form_col2:
                    password = st.text_input("Password (required)", type="password", placeholder="Create password")
                    confirm_password = st.text_input("Confirm Password (required)", type="password", placeholder="Confirm password")
                    age = st.number_input("Age", min_value=13, max_value=120)
                    gender = st.selectbox("Gender", ["Prefer not to say", "Male", "Female", "Other"])

                submit_button = st.form_submit_button("Create Account")
                
                if submit_button:
                    if not (username and email and password and first_name and last_name):
                        st.error("Please fill all required fields")
                    elif password != confirm_password:
                        st.error("Passwords do not match")
                    else:
                        if create_user(username, email, password, first_name, last_name, age, gender):
                            st.success("Account created successfully! Please login.")
                            return True
                        else:
                            st.error("Username or email already exists")
    return False
