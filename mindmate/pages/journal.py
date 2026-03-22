import streamlit as st
from datetime import datetime
from mindmate.utils.database import get_db_connection
from mindmate.utils.mood_analysis import analyze_mood_from_text, detect_keywords
import logging

logger = logging.getLogger(__name__)

ENTRY_TYPES = [
    "Daily Reflection",
    "Gratitude Journal",
    "Emotion Processing",
    "Goal Setting",
    "Free Writing"
]

def save_journal_entry(user_id: str, entry_type: str, content: str, mood_score: int) -> bool:
    """Save journal entry to database"""
    try:
        keywords = ", ".join(detect_keywords(content))
        timestamp = datetime.now()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO journal_entries 
                (user_id, timestamp, entry_type, content, mood_score, keywords)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, timestamp, entry_type, content, mood_score, keywords))
            conn.commit()
            
        return True
    except Exception as e:
        logger.error(f"Failed to save journal entry: {str(e)}")
        return False

def get_recent_entries(user_id: str, limit: int = 5) -> list:
    """Get recent journal entries from database"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    id,
                    timestamp,
                    entry_type,
                    content,
                    mood_score
                FROM journal_entries
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (user_id, limit))
            
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Failed to get journal entries: {str(e)}")
        return []

def show_journal_form(user_id: str):
    """Display form for creating new journal entries"""
    with st.form("journal_form", clear_on_submit=True):
        st.subheader("New Journal Entry")
        
        col1, col2 = st.columns(2)
        
        with col1:
            entry_type = st.selectbox(
                "Entry Type",
                ENTRY_TYPES,
                help="Select the type of journal entry"
            )
        
        with col2:
            mood_score = st.slider(
                "Current Mood",
                min_value=1,
                max_value=10,
                value=5,
                help="Rate your current mood from 1 (very negative) to 10 (very positive)"
            )
        
        content = st.text_area(
            "Write your thoughts...",
            height=200,
            placeholder="Take a moment to reflect on your day, emotions, or anything on your mind..."
        )
        
        submitted = st.form_submit_button("Save Entry")
        
        if submitted:
            if not content.strip():
                st.error("Please write something before saving")
                return
            
            # Analyze mood from text and combine with user's rating
            text_mood = analyze_mood_from_text(content)
            combined_mood = ((mood_score / 5) - 1 + text_mood) / 2  # Scale to -1 to 1 range
            
            if save_journal_entry(user_id, entry_type, content, combined_mood):
                st.success("Entry saved successfully!")
            else:
                st.error("Failed to save entry. Please try again.")

def show_journal_history(user_id: str):
    """Display previous journal entries"""
    st.subheader("Journal History")
    
    entries = get_recent_entries(user_id)
    
    if not entries:
        st.info("No journal entries yet. Start writing to see them here!")
        return
    
    for entry in entries:
        entry_id, timestamp, entry_type, content, mood_score = entry
        
        # Determine mood color
        if mood_score > 0.2:
            mood_color = "#2ecc71"  # Green
        elif mood_score < -0.2:
            mood_color = "#e74c3c"  # Red
        else:
            mood_color = "#f39c12"  # Orange
            
        mood_emoji = "😊" if mood_score > 0.2 else "😐" if mood_score > -0.2 else "😞"
        
        # Ensure timestamp is properly formatted whether it's a string or datetime object
        display_time = timestamp.strftime('%b %d, %Y %I:%M %p') if hasattr(timestamp, 'strftime') else timestamp
        with st.expander(f"{entry_type} • {display_time} • {mood_emoji}"):
            st.markdown(f"""
                <div style="background-color:#f8f9fa;padding:15px;border-radius:10px;margin-bottom:15px">
                    <p style="color:#576574;margin:0;">{content}</p>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <span style="color:{mood_color};font-weight:bold">Mood: {mood_score:.2f}</span>
                    <button style="background-color:#e74c3c;color:white;border:none;padding:4px 8px;border-radius:3px;cursor:pointer;">
                        Delete
                    </button>
                </div>
            """, unsafe_allow_html=True)

def show(user_id: str):
    """Main journal page function"""
    try:
        st.title("Journal")
        st.markdown("""
            <style>
                .stTextArea textarea {
                    min-height: 200px;
                }
            </style>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["New Entry", "Past Entries"])
        
        with tab1:
            show_journal_form(user_id)
        
        with tab2:
            show_journal_history(user_id)
            
    except Exception as e:
        logger.error(f"Error displaying journal page: {str(e)}")
        st.error("An error occurred while loading the journal")
