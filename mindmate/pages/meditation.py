import streamlit as st
from datetime import datetime, timedelta
from utils.database import get_db_connection
import logging
from utils.visualization import plot_meditation_progress

logger = logging.getLogger(__name__)

MEDITATION_TYPES = [
    "Mindfulness",
    "Breathing",
    "Body Scan",
    "Loving-Kindness",
    "Guided Visualization"
]

def save_meditation_session(session_type: str, minutes: int, notes: str) -> bool:
    """Save meditation session to database"""
    try:
        timestamp = datetime.now()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO meditation_sessions 
                (user_id, timestamp, session_type, minutes, notes)
                VALUES (?, ?, ?, ?, ?)
            """, ("default_user", timestamp, session_type, minutes, notes))
            conn.commit()
            
        return True
    except Exception as e:
        logger.error(f"Failed to save meditation session: {str(e)}")
        return False

def get_recent_sessions(limit: int = 5) -> list:
    """Get recent meditation sessions from database"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    id,
                    timestamp,
                    session_type,
                    minutes,
                    notes
                FROM meditation_sessions
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, ("default_user", limit))
            
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Failed to get meditation sessions: {str(e)}")
        return []

def get_weekly_progress() -> list:
    """Get meditation minutes for the past 7 days"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    date(timestamp) as day,
                    SUM(minutes) as minutes
                FROM meditation_sessions
                WHERE user_id = ? AND date(timestamp) BETWEEN ? AND ?
                GROUP BY date(timestamp)
                ORDER BY day
            """, ("default_user", start_date.date(), end_date.date()))
            
            results = cursor.fetchall()
            
            # Fill in missing days with 0 minutes
            date_range = [start_date + timedelta(days=i) for i in range(8)]
            date_str_range = [date.strftime("%Y-%m-%d") for date in date_range]
            
            progress_data = []
            
            # Create a dict of existing data for quick lookup
            existing_data = {row["day"]: row for row in results}
            
            for date_str in date_str_range:
                if date_str in existing_data:
                    row = existing_data[date_str]
                    progress_data.append({
                        "date": date_str,
                        "minutes": row["minutes"]
                    })
                else:
                    progress_data.append({
                        "date": date_str,
                        "minutes": 0
                    })
            
            return progress_data
            
    except Exception as e:
        logger.error(f"Failed to get weekly progress: {str(e)}")
        return []

def show_meditation_form():
    """Display form for logging meditation sessions"""
    with st.form("meditation_form", clear_on_submit=True):
        st.subheader("Log Meditation Session")
        
        col1, col2 = st.columns(2)
        
        with col1:
            session_type = st.selectbox(
                "Meditation Type",
                MEDITATION_TYPES,
                help="Select the type of meditation you practiced"
            )
        
        with col2:
            minutes = st.number_input(
                "Duration (minutes)",
                min_value=1,
                max_value=120,
                value=10,
                help="How many minutes did you meditate?"
            )
        
        notes = st.text_area(
            "Notes",
            height=100,
            placeholder="Any observations or reflections about your session..."
        )
        
        submitted = st.form_submit_button("Save Session")
        
        if submitted:
            if save_meditation_session(session_type, minutes, notes):
                st.success("Session saved successfully!")
            else:
                st.error("Failed to save session. Please try again.")

def show_meditation_history():
    """Display previous meditation sessions"""
    st.subheader("Recent Sessions")
    
    sessions = get_recent_sessions()
    
    if not sessions:
        st.info("No meditation sessions yet. Start practicing to see them here!")
        return
    
    for session in sessions:
        session_id, timestamp, session_type, minutes, notes = session
        
        with st.expander(f"{session_type} • {minutes} min • {timestamp.strftime('%b %d, %Y %I:%M %p')}"):
            if notes:
                st.markdown(f"""
                    <div style="background-color:#f8f9fa;padding:15px;border-radius:10px;margin-bottom:15px">
                        <p style="color:#576574;margin:0;">{notes}</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.info("No notes for this session")
                
            st.button(
                "Delete",
                key=f"delete_{session_id}",
                on_click=lambda: delete_session(session_id),
                type="primary"
            )

def show_meditation_progress():
    """Display meditation progress chart"""
    st.subheader("Weekly Progress")
    
    progress_data = get_weekly_progress()
    fig = plot_meditation_progress(progress_data)
    
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No meditation data available yet")

def delete_session(session_id: int) -> None:
    """Delete a meditation session"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM meditation_sessions
                WHERE id = ? AND user_id = ?
            """, (session_id, "default_user"))
            conn.commit()
            
        st.success("Session deleted successfully!")
    except Exception as e:
        logger.error(f"Failed to delete meditation session: {str(e)}")
        st.error("Failed to delete session. Please try again.")

def show_meditation_page():
    """Main meditation page function"""
    try:
        st.title("Meditation")
        
        tab1, tab2 = st.tabs(["New Session", "Progress"])
        
        with tab1:
            show_meditation_form()
            show_meditation_history()
        
        with tab2:
            show_meditation_progress()
            
    except Exception as e:
        logger.error(f"Error displaying meditation page: {str(e)}")
        st.error("An error occurred while loading the meditation page")
