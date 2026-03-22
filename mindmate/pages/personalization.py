import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from mindmate.utils import db

def show(user_id):
    st.title("Personalized Wellness")
    
    # User profile section
    with st.expander("My Profile"):
        profile = db.get_user_profile(user_id) or {
            '_id': user_id,
            'name': '',
            'concerns': [],
            'about': '',
            'created_at': datetime.now()
        }
        
        try:
            if not db.get_user_profile(user_id):
                db.update_user_profile(user_id, profile)
                st.info("Welcome! Please complete your profile.")
        except Exception as e:
            st.error(f"Failed to create profile: {str(e)}")
            return
            
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Name", value=profile.get('name', ''), key='profile_name')
            st.selectbox("Age Group", 
                        options=["18-25", "26-35", "36-45", "46-55", "56+"],
                        index=0, key='profile_age')
        with col2:
            st.multiselect("Primary Concerns",
                          options=["Anxiety", "Depression", "Stress", "Sleep", "Relationships"],
                          default=profile.get('concerns', []),
                          key='profile_concerns')
            st.text_area("About Me", value=profile.get('about', ''), key='profile_about')
        
        if st.button("Save Profile"):
            try:
                db.update_user_profile(user_id, {
                    'name': st.session_state.profile_name,
                    'age': st.session_state.profile_age,
                    'concerns': st.session_state.profile_concerns,
                    'about': st.session_state.profile_about,
                    'updated_at': datetime.now()
                })
                st.success("Profile saved!")
            except Exception as e:
                st.error(f"Failed to save profile: {str(e)}")
    
    # Therapist Matching Section
    st.header("🧑‍⚕️ Find Your Therapist")
    
    # Check if user already has a therapist
    current_therapist = db.get_client_therapist(user_id)
    if current_therapist:
        # current_therapist already contains the full therapist document
        therapist_name = current_therapist.get('name') or current_therapist.get('username', 'Unknown')
        st.info(f"Your current therapist: **{therapist_name}**")
        
        # Show current therapist details and messaging interface
        col1, col2 = st.columns([1, 2])
        
        with col1:
            with st.expander("Therapist Details", expanded=True):
                specialties = current_therapist.get('specialties', [])
                st.write(f"**Specialties:** {', '.join(specialties) if specialties else 'Not specified'}")
                st.write(f"**Bio:** {current_therapist.get('bio', 'No bio available')}")
                st.write(f"**Contact:** {current_therapist.get('email', 'Contact info not available')}")
        
        with col2:
            st.subheader("Message Your Therapist")
            try:
                messages = db.get_messages(user_id, current_therapist['_id'], sort_asc=True)
                if messages:
                    # Display message history
                    for msg in messages:
                        is_sent = msg['sender_id'] == user_id
                        with st.chat_message("user" if is_sent else "assistant"):
                            st.write(msg.get('content', ''))
                            st.caption(msg['timestamp'].strftime('%Y-%m-%d %H:%M'))
                else:
                    st.info("No messages yet. Start the conversation!")
                
                # New message input
                new_message = st.text_area("Type your message", key="new_message")
                if st.button("Send Message"):
                    if new_message.strip():
                        try:
                            db.save_message(
                                sender_id=user_id,
                                recipient_id=current_therapist['_id'],
                                content=new_message
                            )
                            st.success("Message sent!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to send message: {str(e)}")
                    else:
                        st.warning("Message cannot be empty")
            except Exception as e:
                st.error(f"Error loading messages: {str(e)}")

        # Message functionality is now integrated above
    else:
        # Show available therapists
        available_therapists = db.get_available_therapists()
        if available_therapists:
            st.subheader("Available Therapists")
            
            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                specialty_filter = st.multiselect(
                    "Filter by specialty",
                    options=["Anxiety", "Depression", "Relationships", "Trauma", "General"],
                    key="specialty_filter"
                )
            
            # Display therapists
            for therapist in available_therapists:
                if not specialty_filter or any(s in therapist.get('profile', {}).get('specialties', []) 
                                            for s in specialty_filter):
                    with st.expander(f"Dr. {therapist.get('name', 'Unknown Therapist')}", expanded=False):
                        st.write(f"**Specialties:** {', '.join(therapist.get('profile', {}).get('specialties', []))}")
                        st.write(f"**Bio:** {therapist.get('profile', {}).get('bio', 'No bio available')}")
                        
                    # Check if already requested
                    existing_request = db.get_pending_requests(therapist['_id'])
                    if any(req['client_id'] == user_id for req in existing_request):
                        st.info("Request pending")
                    else:
                        with st.form(key=f"therapist_request_form_{therapist['_id']}"):
                            profile = db.get_user_profile(user_id) or {}
                            name = st.text_input("Your Name", 
                                                   value=profile.get('name', ''), 
                                                   key=f"name_{therapist['_id']}")
                            email = st.text_input("Email", 
                                                    value=profile.get('email', ''),
                                                    key=f"email_{therapist['_id']}")
                            phone = st.text_input("Phone Number", 
                                                    key=f"phone_{therapist['_id']}")
                            col1, col2 = st.columns(2)
                            with col1:
                                preferred_date = st.date_input("Preferred Date",
                                                                min_value=datetime.now().date(),
                                                                key=f"date_{therapist['_id']}")
                                if preferred_date < datetime.now().date():
                                    st.error("Please select a future date")
                            with col2:
                                preferred_time = st.time_input("Preferred Time (9am-5pm)",
                                                                key=f"time_{therapist['_id']}")
                                if preferred_time and (preferred_time < datetime.strptime("09:00", "%H:%M").time() or 
                                                    preferred_time > datetime.strptime("17:00", "%H:%M").time()):
                                    st.error("Please select a time between 9am and 5pm")
                            problem_description = st.text_area(
                                "Describe your concerns (will be shared with therapist)",
                                key=f"request_{therapist['_id']}"
                            )
                            
                            if st.form_submit_button("Request Therapist"):
                                # Validate date/time before submission
                                valid_date = preferred_date >= datetime.now().date()
                                valid_time = (preferred_time >= datetime.strptime("09:00", "%H:%M").time() and 
                                            preferred_time <= datetime.strptime("17:00", "%H:%M").time())
                                
                                if all([name.strip(), email.strip(), phone.strip(), problem_description.strip()]) and valid_date and valid_time:
                                    db.send_therapist_request(
                                        client_id=user_id,
                                        therapist_id=therapist['_id'],
                                        client_name=name,
                                        client_email=email,
                                        client_phone=phone,
                                        preferred_date=preferred_date,
                                        preferred_time=preferred_time,
                                        problem_description=problem_description
                                    )
                                    st.success("Request sent! The therapist will review your request.")
                                else:
                                    st.error("Please fill in all required fields")
        else:
            st.info("No therapists available at the moment. Please check back later.")
    
    # Personalized recommendations
    st.header("Your Recommendations")
    mood_data = db.get_mood_history(user_id)
    if len(mood_data) > 7:
        analyze_mood_patterns(mood_data)
        show_personalized_content(mood_data)
    else:
        st.info("We need more mood data (at least 7 days) to provide personalized recommendations")
    
    # Crisis resources
    st.header("Quick Access Resources")
    show_crisis_resources()

def analyze_mood_patterns(mood_data):
    df = pd.DataFrame(mood_data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    
    st.subheader("Your Mood Patterns")
    col1, col2 = st.columns(2)
    with col1:
        st.line_chart(df['mood_score'])
    with col2:
        avg_mood = df['mood_score'].mean()
        st.metric("Average Mood", f"{avg_mood:.1f}/10")
        worst_day = df['mood_score'].idxmin().strftime('%A')
        st.metric("Toughest Day", worst_day)

def show_personalized_content(mood_data):
    df = pd.DataFrame(mood_data)
    avg_mood = df['mood_score'].mean()
    
    if avg_mood < 5:
        st.warning("We notice you've been feeling down lately. Here are some resources:")
        st.markdown("- [Cognitive Behavioral Therapy exercises]()")
        st.markdown("- [Guided meditation for low mood]()")
    else:
        st.success("Great job maintaining your wellness! Keep it up with these resources:")
        st.markdown("- [Mindfulness exercises]()")
        st.markdown("- [Gratitude journal prompts]()")

def show_crisis_resources():
    resources = [
        {"name": "Suicide Prevention Lifeline", "phone": "988", "url": "https://988lifeline.org"},
        {"name": "Crisis Text Line", "text": "HOME to 741741", "url": "https://www.crisistextline.org"},
        {"name": "NAMI Helpline", "phone": "800-950-NAMI", "url": "https://www.nami.org/help"}
    ]
    
    for resource in resources:
        with st.expander(resource['name']):
            if 'phone' in resource:
                st.markdown(f"Phone: {resource['phone']}")
            if 'text' in resource:
                st.markdown(f"Text: {resource['text']}")
            st.markdown(f"[Website]({resource['url']})")
