import streamlit as st
from datetime import datetime
from mindmate.utils.database import get_db_connection
import logging

logger = logging.getLogger(__name__)

def record_meditation_session():
    """Form to record a new meditation session"""
    with st.form("meditation_form"):
        st.subheader("Record Meditation Session")
        
        session_type = st.selectbox(
            "Session Type",
            ["Breathing", "Mindfulness", "Body Scan", "Loving-Kindness", "Other"]
        )
        
        minutes = st.number_input(
            "Duration (minutes)",
            min_value=1,
            max_value=120,
            value=10
        )
        
        notes = st.text_area("Notes (optional)")
        
        submitted = st.form_submit_button("Save Session")
        
        if submitted:
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        INSERT INTO meditation_sessions 
                        (user_id, timestamp, session_type, minutes, notes)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        ("default_user", datetime.now(), session_type, minutes, notes)
                    )
                    conn.commit()
                
                st.success("Meditation session recorded successfully!")
            except Exception as e:
                logger.error(f"Failed to record meditation session: {str(e)}")
                st.error("Failed to save meditation session")

def show_recent_sessions():
    """Display recent meditation sessions"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT timestamp, session_type, minutes, notes
                FROM meditation_sessions
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 5
                """,
                ("default_user",)
            )
            sessions = cursor.fetchall()
            
        if sessions:
            st.subheader("Recent Sessions")
            for session in sessions:
                st.markdown(f"""
                    <div style="background-color:#f8f9fa;padding:15px;border-radius:10px;margin-bottom:10px">
                        <p style="margin:0;font-weight:bold">
                            {session['session_type']} • {session['minutes']} minutes
                        </p>
                        <p style="margin:0;color:#666">
                            {session['timestamp']}
                        </p>
                        {f"<p style='margin:0;margin-top:5px'>{session['notes']}</p>" if session['notes'] else ""}
                    </div>
                """, unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Failed to fetch meditation sessions: {str(e)}")


def show(user_id):
    """Main meditation tracker page"""
    st.title("🧘 Meditation Tracker")
    
    record_meditation_session()
    
    show_recent_sessions()
