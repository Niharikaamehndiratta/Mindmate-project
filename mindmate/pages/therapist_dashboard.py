import streamlit as st
from datetime import datetime, timedelta
from mindmate.utils import db
import plotly.express as px

def show_dashboard():
    st.title("Therapist Dashboard")
    
    therapist_id = db.get_therapist_id(st.session_state.therapist_email)
    clients = db.get_therapist_clients(therapist_id)
    
    # Stats cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Clients", len(clients))
    with col2:
        active_clients = len([c for c in clients if c.get('last_active') and 
                            c['last_active'] != 'Never' and 
                            (datetime.now() - datetime.strptime(c['last_active'], '%Y-%m-%d %H:%M:%S')).days < 7])
        st.metric("Active Clients", active_clients)
    with col3:
        st.metric("Unread Messages", db.get_unread_count(therapist_id))
    
    # Enhanced sidebar
    with st.sidebar:
        st.subheader("Quick Actions")
        if st.button("📝 New Session Note", key="new_note_btn"):
            st.session_state.show_session_note = True
        if st.button("👥 View All Clients", key="view_patients_btn"):
            st.session_state.show_patient_list = True
        if st.button("📊 View Analytics", key="analytics_btn"):
            st.session_state.show_analytics = True
        if st.button("⚙️ Settings", key="settings_btn"):
            st.session_state.show_settings = True
        if st.button("🚪 Logout", key="logout_btn"):
            st.session_state.therapist_logged_in = False
            st.rerun()

    # Main dashboard content
    tab1, tab2, tab3, tab4 = st.tabs(["Client Overview", "Patient Requests", "Activity Feed", "Messaging"])
    
    with tab1:
        st.subheader("Client Overview")
        
    with tab2:
        st.subheader("Patient Requests")
        pending_requests = db.get_pending_requests(therapist_id)
        
        if pending_requests:
            for request in pending_requests:
                with st.expander(f"Request from {request.get('client_name', 'Unknown')}"):
                    st.write(f"**Email:** {request['client_email']}")
                    st.write(f"**Phone:** {request['client_phone']}")
                    st.write(f"**Preferred Date:** {request['preferred_date'].strftime('%Y-%m-%d')}")
                    st.write(f"**Preferred Time:** {request['preferred_time'].strftime('%H:%M')}")
                    st.write(f"**Concerns:** {request['problem_description']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Accept", key=f"accept_{request['_id']}"):
                            try:
                                db.update_request_status(request['_id'], "Accepted")
                                db.assign_therapist(request['client_id'], therapist_id)
                                db.log_notification(
                                    request['client_id'],
                                    "request_accepted",
                                    f"Your therapist request has been accepted by Dr. {st.session_state.therapist_email.split('@')[0]}"
                                )
                                st.success("Request accepted!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error accepting request: {str(e)}")
                    
                    with col2:
                        if st.button("Decline", key=f"decline_{request['_id']}"):
                            try:
                                db.update_request_status(request['_id'], "Declined")
                                db.log_notification(
                                    request['client_id'],
                                    "request_declined",
                                    f"Your therapist request has been declined by Dr. {st.session_state.therapist_email.split('@')[0]}"
                                )
                                st.success("Request declined!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error declining request: {str(e)}")
        else:
            st.info("No pending patient requests")
        if clients:
            selected_client = st.selectbox(
                "Select Patient",
                options=[c['id'] for c in clients],
                format_func=lambda x: next(c['name'] for c in clients if c['id'] == x)
            )
            
            # Get client info from the existing clients list
            client_info = next((c for c in clients if c['id'] == selected_client), None)
            if client_info:
                st.write(f"**Name:** {client_info['name']}")
                st.write(f"**Last Active:** {client_info['last_active']}")
                st.write(f"**Session Count:** {client_info['session_count']}")
            
            if st.button("View Activity", key=f"view_activity_{selected_client}"):
                st.session_state.view_client_activity = selected_client
        else:
            st.info("You don't have any assigned patients yet")

    with tab3:
        st.subheader("Activity Feed")
        try:
            activity = db.get_recent_activity(therapist_id)
            if activity:
                for event in activity:
                    with st.expander(
                        f"📍 {event['type'].title()} - {event['timestamp'].strftime('%Y-%m-%d %H:%M')}",
                        expanded=False
                    ):
                        st.markdown(f"**{event['description']}**")
                        st.write(event['content'])
                        if event['type'] == 'message':
                            st.button("💬 Reply", key=f"reply_{event.get('id')}")
            else:
                st.info("No recent activity found")
        except Exception as e:
            st.error(f"Error loading activity: {str(e)}")
            
    with tab4:
        st.subheader("Messaging")
        if clients:
            selected_client = st.selectbox(
                "Select Patient to Message",
                options=[c['id'] for c in clients],
                format_func=lambda x: next(c['name'] for c in clients if c['id'] == x),
                key="message_client_select"
            )
            
            # Display message history
            messages = db.get_messages(therapist_id, selected_client)
            for msg in sorted(messages, key=lambda x: x['timestamp']):
                is_sent = msg['sender_id'] == therapist_id
                align = "right" if is_sent else "left"
                with st.chat_message("user", avatar="🧑‍⚕️" if is_sent else "👤"):
                    st.markdown(f"**{msg['content']}**")
                    timestamp = msg['timestamp'].strftime('%Y-%m-%d %H:%M')
                    st.caption(f"{timestamp} {'✓✓' if msg.get('read', False) else '✓'}")
            
            # New message input
            new_message = st.text_area("New Message", key=f"new_msg_{selected_client}")
            if st.button("Send", key=f"send_{selected_client}"):
                if new_message.strip():
                    db.save_message(
                        sender_id=therapist_id,
                        recipient_id=selected_client,
                        content=new_message
                    )
                    st.rerun()
        else:
            st.info("No patients available for messaging")

    # Analytics section
    if st.session_state.get('show_analytics'):
        st.subheader("Client Analytics")
        if clients:
            fig = px.bar(
                x=[c['name'] for c in clients],
                y=[c.get('session_count', 0) for c in clients],
                labels={'x': 'Client', 'y': 'Sessions'},
                title="Session Count by Client"
            )
            st.plotly_chart(fig, use_container_width=True)

    # Session notes modal
    if st.session_state.get('show_session_note'):
        with st.expander("New Session Note", expanded=True):
            client = st.selectbox(
                "Patient",
                options=[c['id'] for c in clients],
                format_func=lambda x: next(c['name'] for c in clients if c['id'] == x)
            )
            note = st.text_area("Session Notes")
            if st.button("Save Note", key="save_note_btn"):
                db.save_session_note(
                    therapist_id=therapist_id,
                    client_id=client,
                    note=note,
                    date=datetime.now()
                )
                st.success("Note saved!")
                st.session_state.show_session_note = False
                st.rerun()
            if st.button("Cancel", key="cancel_note_btn"):
                st.session_state.show_session_note = False
                st.rerun()
