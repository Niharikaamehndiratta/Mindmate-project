import streamlit as st
from mindmate.utils import db

def show(user_id: str = None, therapist_mode: bool = False):
    """Show registered MindMate therapists or therapist view
    
    Args:
        user_id: Required for patient view, optional for therapist view
        therapist_mode: Whether to show therapist-specific interface
    """
    st.title("👩‍⚕️ Find a Therapist")
    st.markdown("Browse and connect with our approved mental health professionals")
    
    # Therapist directory section
    st.header("Available Therapists")
    
    # Get available therapists from MongoDB
    therapists = db.get_available_therapists()
    
    if not therapists:
        st.warning("No therapists currently available. Please check back later.")
        return
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        specialty_filter = st.multiselect(
            "Filter by specialty",
            options=list(set([s for t in therapists for s in t.get('profile', {}).get('specialties', [])])),
            default=[]
        )
    
    # Apply filters
    filtered_therapists = therapists
    if specialty_filter:
        filtered_therapists = [t for t in filtered_therapists 
                             if any(s in t.get('profile', {}).get('specialties', []) 
                                   for s in specialty_filter)]
    
    # Display therapist profiles
    for therapist in filtered_therapists:
        profile = therapist.get('profile', {})
        with st.expander(f"👤 {therapist['name']} - {', '.join(profile.get('specialties', []))}"):
            col1, col2 = st.columns([1, 3])
            
            with col1:
                photo_url = profile.get('photo_url')
                if photo_url:
                    st.image(photo_url, width=150)
                else:
                    st.image("https://via.placeholder.com/150", width=150)
            
            with col2:
                st.markdown(f"**Specialties:** {', '.join(profile.get('specialties', []))}")
                st.markdown(f"**Approach:** {profile.get('modality', 'Not specified')}")
                st.markdown(f"**Languages:** {', '.join(profile.get('languages', ['English']))}")
                st.markdown(f"**Availability:** {profile.get('availability', 'Contact for availability')}")
                st.markdown(f"**Credentials:** {profile.get('credentials', 'Licensed Professional')}")
                st.markdown(f"**About:** {profile.get('bio', 'No bio available')}")
                
                if not therapist_mode and user_id:
                    # Appointment request form (only shown for patients with valid user_id)
                    with st.form(key=f"appointment_{therapist['_id']}"):
                        name = st.text_input("Your Name", key=f"name_{therapist['_id']}")
                        email = st.text_input("Email", key=f"email_{therapist['_id']}")
                        phone = st.text_input("Phone", key=f"phone_{therapist['_id']}")
                        preferred_date = st.date_input("Preferred Date", key=f"date_{therapist['_id']}")
                        preferred_time = st.time_input("Preferred Time", key=f"time_{therapist['_id']}")
                        concerns = st.text_area("Briefly describe your concerns", key=f"concerns_{therapist['_id']}")
                        
                        if st.form_submit_button("Request Appointment"):
                            try:
                                db.send_therapist_request(
                                    client_id=user_id,
                                    therapist_id=therapist['_id'],
                                    client_name=name,
                                    client_email=email,
                                    client_phone=phone,
                                    preferred_date=preferred_date,
                                    preferred_time=preferred_time,
                                    problem_description=concerns
                                )
                                st.success("Request sent! The therapist will review your request.")
                            except Exception as e:
                                st.error(f"Error submitting request: {str(e)}")
