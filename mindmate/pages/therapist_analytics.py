import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from mindmate.utils import db
from bson import ObjectId

def show():
    st.title("Therapist Analytics Dashboard")
    
    if 'therapist_id' not in st.session_state:
        st.error("Please log in again.")
        return
        
    therapist_id = st.session_state.therapist_id
    
    # Create tabs for different analytics views
    tab1, tab2, tab3, tab4 = st.tabs([
        "Patient Overview", 
        "Session Analytics", 
        "Treatment Progress",
        "Engagement Metrics"
    ])
    
    with tab1:
        show_patient_overview(therapist_id)
        
    with tab2:
        show_session_analytics(therapist_id)
        
    with tab3:
        show_treatment_progress(therapist_id)
        
    with tab4:
        show_engagement_metrics(therapist_id)

def show_patient_overview(therapist_id):
    st.subheader("Patient Overview")
    
    # Get all patients
    patients = db.get_therapist_clients(therapist_id)
    total_patients = len(patients)
    
    # Create metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Patients", total_patients)
    with col2:
        active_last_week = sum(1 for p in patients if p['last_active'] and 
                              isinstance(p['last_active'], datetime) and
                              p['last_active'] > datetime.now() - timedelta(days=7))
        st.metric("Active Past Week", active_last_week)
    with col3:
        avg_sessions = sum(p['session_count'] for p in patients) / total_patients if total_patients > 0 else 0
        st.metric("Avg Sessions/Patient", f"{avg_sessions:.1f}")
    
    # Patient Status Distribution
    status_data = {
        'New (0-1 sessions)': sum(1 for p in patients if p['session_count'] <= 1),
        'Regular (2-10 sessions)': sum(1 for p in patients if 2 <= p['session_count'] <= 10),
        'Long-term (>10 sessions)': sum(1 for p in patients if p['session_count'] > 10)
    }
    
    fig = px.pie(
        values=list(status_data.values()),
        names=list(status_data.keys()),
        title="Patient Distribution by Status"
    )
    st.plotly_chart(fig)

def show_session_analytics(therapist_id):
    st.subheader("Session Analytics")
    
    # Time period selector
    period = st.selectbox(
        "Select Time Period",
        ["Last Week", "Last Month", "Last 3 Months", "Last Year"]
    )
    
    # Get session data
    sessions = db.get_collection('session_notes').find({
        'therapist_id': ObjectId(therapist_id)
    })
    
    # Convert to DataFrame
    df = pd.DataFrame(list(sessions))
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        
        # Session frequency over time
        fig = px.line(
            df.groupby('date').size().reset_index(name='count'),
            x='date',
            y='count',
            title="Session Frequency Over Time"
        )
        st.plotly_chart(fig)
        
        # Session duration distribution
        if 'duration' in df.columns:
            fig = px.histogram(
                df,
                x='duration',
                title="Session Duration Distribution (minutes)"
            )
            st.plotly_chart(fig)
    else:
        st.info("No session data available for the selected period")

def show_treatment_progress(therapist_id):
    st.subheader("Treatment Progress")
    
    # Patient selector
    patients = db.get_therapist_clients(therapist_id)
    if not patients:
        st.info("No patients available")
        return
        
    selected_patient = st.selectbox(
        "Select Patient",
        options=[p['id'] for p in patients],
        format_func=lambda x: next(p['name'] for p in patients if p['id'] == x)
    )
    
    # Get mood history
    mood_data = db.get_mood_history(selected_patient)
    if mood_data:
        df = pd.DataFrame(mood_data)
        df['date'] = pd.to_datetime(df['date'])
        
        # Mood trend
        fig = px.line(
            df,
            x='date',
            y='mood_score',
            title="Patient Mood Trend"
        )
        st.plotly_chart(fig)
        
        # Treatment milestones
        st.subheader("Treatment Milestones")
        milestones = [
            {"date": "2024-01-15", "event": "Started therapy"},
            {"date": "2024-02-01", "event": "Completed initial assessment"},
            {"date": "2024-03-01", "event": "Treatment plan review"}
        ]
        
        for milestone in milestones:
            st.markdown(f"**{milestone['date']}**: {milestone['event']}")
    else:
        st.info("No mood data available for this patient")

def show_engagement_metrics(therapist_id):
    st.subheader("Engagement Metrics")
    
    # Get all patients
    patients = db.get_therapist_clients(therapist_id)
    
    # Message response time analysis
    messages = db.get_collection('messages').find({
        '$or': [
            {'sender_id': therapist_id},
            {'recipient_id': therapist_id}
        ]
    })
    
    if messages:
        df = pd.DataFrame(list(messages))
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Average response time
        response_times = []
        for patient in patients:
            patient_messages = df[
                (df['sender_id'].isin([therapist_id, patient['id']])) &
                (df['recipient_id'].isin([therapist_id, patient['id']]))
            ].sort_values('timestamp')
            
            if len(patient_messages) > 1:
                response_time = (patient_messages['timestamp'] - patient_messages['timestamp'].shift()).mean()
                response_times.append({
                    'patient': patient['name'],
                    'avg_response_time': response_time.total_seconds() / 3600  # Convert to hours
                })
        
        if response_times:
            response_df = pd.DataFrame(response_times)
            fig = px.bar(
                response_df,
                x='patient',
                y='avg_response_time',
                title="Average Response Time by Patient (Hours)"
            )
            st.plotly_chart(fig)
    
    # Session attendance rate
    st.subheader("Session Attendance Rate")
    attendance_data = {
        'Attended': 85,
        'Cancelled': 10,
        'No-show': 5
    }
    
    fig = px.pie(
        values=list(attendance_data.values()),
        names=list(attendance_data.keys()),
        title="Session Attendance Distribution"
    )
    st.plotly_chart(fig)

if __name__ == "__main__":
    show()
