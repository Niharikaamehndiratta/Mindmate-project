import streamlit as st
from mindmate.utils import db
from mindmate.utils.validators import validate_therapist_credentials

def show_login():
    st.title("Therapist Portal")
    st.subheader("Login")

    with st.form("therapist_login"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            if validate_therapist_credentials(email, password):
                therapist_id = db.get_therapist_id(email)
                if therapist_id:
                    st.session_state.therapist_logged_in = True
                    st.session_state.therapist_email = email
                    st.session_state.therapist_id = therapist_id
                    st.rerun()
                else:
                    st.error("Failed to retrieve therapist ID")
            else:
                st.error("Invalid credentials")

    if st.button("New Therapist? Register Here"):
        st.session_state.show_register = True
        st.rerun()

def show_register():
    st.title("Therapist Registration")
    st.subheader("Create Account")

    with st.form("therapist_register"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        license_number = st.text_input("License Number")
        specialization = st.selectbox(
            "Specialization",
            ["Clinical Psychology", "Counseling", "Psychiatry", "Other"]
        )
        years_experience = st.number_input("Years of Experience", min_value=0)
        bio = st.text_area("Professional Bio")
        
        submitted = st.form_submit_button("Register")

        if submitted:
            if password != confirm_password:
                st.error("Passwords don't match")
            elif db.therapist_exists(email):
                st.error("Email already registered")
            else:
                db.register_therapist(
                    name=name,
                    email=email,
                    password=password,
                    license_number=license_number,
                    specialization=specialization,
                    years_experience=years_experience,
                    bio=bio
                )
                st.success("Registration successful! Please login.")
                st.session_state.show_register = False
                st.rerun()

    if st.button("Already registered? Login Here"):
        st.session_state.show_register = False
        st.rerun()

def show():
    if 'therapist_logged_in' not in st.session_state:
        st.session_state.therapist_logged_in = False
    if 'show_register' not in st.session_state:
        st.session_state.show_register = False

    if st.session_state.therapist_logged_in:
        from .therapist_dashboard import show_dashboard
        show_dashboard()
    else:
        if st.session_state.show_register:
            show_register()
        else:
            show_login()
