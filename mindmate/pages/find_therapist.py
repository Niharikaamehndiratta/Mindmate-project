import streamlit as st
from datetime import datetime
from mindmate.utils import db

def show(user_id):
    # Check if user has an accepted therapist
    therapist_info = db.get_accepted_therapist(user_id)
    
    if therapist_info:
        show_messaging_interface(user_id, therapist_info)
    elif db.has_pending_request(user_id):
        show_pending_view(user_id)
    else:
        show_search_interface(user_id)

def show_search_interface(user_id):
    st.title("Find a Therapist")
    
    # Search filters
    col1, col2 = st.columns(2)
    with col1:
        specialization = st.selectbox(
            "Specialization",
            options=["Anxiety", "Depression", "Relationships", "Trauma", "Stress"]
        )
    with col2:
        language = st.selectbox(
            "Language",
            options=["English", "Spanish", "French", "German", "Mandarin"]
        )
    
    # Search button
    if st.button("Search Therapists"):
        therapists = db.search_therapists(specialization, language)
        
        if therapists:
            st.subheader("Available Therapists")
            for therapist in therapists:
                with st.expander(f"{therapist['name']} - {therapist['specialization']}"):
                    st.write(f"**Bio:** {therapist['bio']}")
                    st.write(f"**Languages:** {therapist['languages']}")
                    st.write(f"**Availability:** {therapist['availability']}")
                    
                    if st.button("Request Session", key=f"request_{therapist['_id']}"):
                        if db.request_therapist(user_id, therapist['_id']):
                            st.success("Request sent! The therapist will review your request.")
                            st.rerun()
                        else:
                            st.error("Failed to send request. Please try again.")
        else:
            st.warning("No therapists found matching your criteria")

def show_pending_view(user_id):
    st.title("Therapist Request Status")
    pending_requests = db.get_pending_therapist_requests(user_id)
    
    if pending_requests:
        for req in pending_requests:
            st.write(f"Request to {req['therapist_name']} - Status: {req['status']}")
            if st.button("Cancel Request", key=f"cancel_{req['_id']}"):
                if db.cancel_therapist_request(req['_id']):
                    st.rerun()
    else:
        st.info("No pending therapist requests")
        if st.button("Find a Therapist"):
            show_search_interface(user_id)

def show_messaging_interface(user_id, therapist_info):
    st.title(f"Messaging with {therapist_info['name']}")
    
    # Display message history
    messages = db.get_messages(user_id, therapist_info['_id'])
    display_message_history(messages, user_id)
    
    # New message input
    new_message = st.text_area("New Message", key="new_message")
    
    if st.button("Send"):
        if new_message.strip():
            db.save_message(
                sender_id=user_id,
                recipient_id=therapist_info['_id'],
                message=new_message,
                timestamp=datetime.now()
            )
            st.success("Message sent!")
            st.rerun()
        else:
            st.warning("Message cannot be empty")

def display_message_history(messages, current_user_id):
    """Display message history in a chat-like interface"""
    st.divider()
    
    for msg in sorted(messages, key=lambda x: x['timestamp']):
        is_sent = msg['sender_id'] == current_user_id
        align = "right" if is_sent else "left"
        color = "primary" if is_sent else "secondary"
        
        with st.chat_message("user", avatar="🧑‍⚕️" if not is_sent else "👤"):
            st.markdown(f"**{msg['message']}**")
            timestamp = msg['timestamp'].strftime('%Y-%m-%d %H:%M')
            if is_sent:
                read_status = "✓✓" if msg.get('read', False) else "✓"
                st.caption(f"{timestamp} {read_status}")
            else:
                st.caption(f"{timestamp}")
