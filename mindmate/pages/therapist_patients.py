import streamlit as st
from mindmate.utils import db
from bson import ObjectId
from pprint import pformat

def show():
    st.title("Patient Management")
    
    if 'therapist_id' not in st.session_state:
        st.error("Please log in again.")
        return
        
    therapist_id = st.session_state.therapist_id
    
    # Verify therapist_id is valid ObjectId
    if not isinstance(therapist_id, ObjectId):
        try:
            therapist_id = ObjectId(therapist_id)
            st.session_state.therapist_id = therapist_id
        except Exception as e:
            st.error(f"Invalid therapist_id format: {e}")
            return
    
    # Show pending requests section
    st.subheader("Pending Requests")
    try:
        requests = list(db.get_collection('therapist_requests').find({
            'therapist_id': therapist_id,
            'status': 'pending'
        }))
        
    except Exception as e:
        st.error(f"Failed to fetch requests: {e}")
        requests = []
    
    if requests:
        for req in requests:
            with st.expander(f"Request from {req['client_name']}"):
                st.write(f"**Email:** {req['client_email']}")
                st.write(f"**Phone:** {req['client_phone']}")
                st.write(f"**Preferred Date:** {req['appointment_datetime'].strftime('%Y-%m-%d')}")
                st.write(f"**Concerns:** {req['problem_description']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Accept", key=f"accept_{req['_id']}"):
                        with st.spinner("Processing acceptance..."):
                            try:
                                db.update_request_status(req['_id'], 'accepted')
                                db.assign_therapist(
                                    req['client_id'],
                                    therapist_id,
                                    client_name=req['client_name'],
                                    client_email=req['client_email']
                                )
                                st.session_state.last_accepted = req['client_id']
                                st.success("Request accepted! Patient added to your list.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to accept request: {str(e)}")
                with col2:
                    if st.button("Decline", key=f"decline_{req['_id']}"):
                        db.update_request_status(req['_id'], 'declined')
                        st.success("Request declined.")
                        st.rerun()
    else:
        st.info("No pending requests")
    
    # Show current patients section
    st.subheader("Your Patients")
    if 'last_accepted' in st.session_state:
        st.success(f"Successfully accepted patient {st.session_state.last_accepted}")
        del st.session_state.last_accepted
    
    try:
        # Get total client count for pagination
        total_clients = db.get_client_count(therapist_id)
        
        # Add pagination controls if needed
        page_size = 10
        if total_clients > page_size:
            page = st.number_input("Page", min_value=1, max_value=(total_clients // page_size) + 1, value=1)
            skip = (page - 1) * page_size
        else:
            skip = 0
            
        # Fetch patients with pagination
        patients = db.get_therapist_clients(therapist_id, limit=page_size, skip=skip)
    except Exception as e:
        st.error(f"Failed to load patients: {str(e)}")
        patients = []
        
    if patients:
        st.write(f"Showing {len(patients)} of {total_clients} total patients")
        for patient in patients:
            # Format last session date
            last_session = patient.get('last_session', 'No sessions yet')
            if last_session and last_session != 'No sessions yet':
                last_session = last_session.strftime("%Y-%m-%d")
                
            patient_idx = patients.index(patient)
            with st.expander(f"{patient['name']} - Last Session: {last_session}"):
                    st.write(f"**Email:** {patient['email']}")
                    st.write(f"**Session Count:** {patient['session_count']}")
                    st.write(f"**Last Active:** {patient['last_active']}")
                    assigned_date = patient.get('assigned_at')
                    st.write(f"**Assigned Since:** {assigned_date.strftime('%Y-%m-%d') if assigned_date else 'Not available'}")
                    st.write(f"**Last Note:** {patient['last_note'][:100]}..." if patient['last_note'] else "No notes yet")
                
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("View Profile", key=f"view_{patient['id']}_{patient_idx}"):
                            st.session_state.view_patient = patient['id']
                            st.switch_page("pages/patient_profile.py")
                    with col2:
                        if st.button("Message", key=f"msg_{patient['id']}_{patient_idx}"):
                            st.session_state.current_chat = patient['id']
                            st.switch_page("pages/personalization.py")
                    with col3:
                        if st.button("Remove", key=f"remove_{patient['id']}_{patient_idx}"):
                            try:
                                db.remove_therapist_relationship(patient['id'], therapist_id)
                                st.success(f"Removed {patient['name']} from your patient list")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to remove patient: {str(e)}")
    else:
        st.info("You don't have any assigned patients yet")
        
    if st.button("Back to Dashboard"):
        st.switch_page("pages/therapist_dashboard.py")
