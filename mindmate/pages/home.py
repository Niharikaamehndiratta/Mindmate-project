import streamlit as st
from datetime import datetime, timedelta
from mindmate.utils.database import get_db_connection
from mindmate.utils import db
from mindmate.utils.stats_manager import StatsManager
from mindmate.utils.visualization import display_visualizations
import logging

logger = logging.getLogger(__name__)

def show_welcome_banner():
    """Display welcome banner with personalized greeting"""
    current_hour = datetime.now().hour
    if 5 <= current_hour < 12:
        greeting = "Good morning"
    elif 12 <= current_hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"
    
    st.markdown(f"""
        <div style="background-color:#f0f2f6;padding:20px;border-radius:10px;margin-bottom:20px">
            <h1 style="color:#2e86de;margin:0;">{greeting}! 👋</h1>
            <p style="color:#576574;margin:0;">Welcome to your MindMate dashboard</p>
        </div>
    """, unsafe_allow_html=True)

def show_quick_stats(user_id: str):
    """Display quick stats cards with independent refresh"""
    stats_manager = StatsManager(user_id)
    
    col1, col2, col3 = st.columns([1,1,1])
    
    with col1:
        if st.button('🔄 Refresh Journal Stats'):
            stats_manager.refresh_stats(force=True)
            st.rerun()
    
    with col2:
        if st.button('👨‍⚕️ Find Therapist'):
            st.switch_page("pages/find_therapist.py")
    
    with col3:
        if st.button('🔄 Refresh Meditation Stats'):
            stats_manager.refresh_stats(force=True)
            st.rerun()
    
    stats = stats_manager.get_all_stats()
    journal_stats = stats['journal'] or {'total_entries': 0, 'avg_mood': 0}
    meditation_stats = stats['meditation'] or {'total_minutes': 0}
    
    # Detailed debug output
    logger.debug(f"Raw journal stats: {stats['journal']}")
    logger.debug(f"Raw meditation stats: {stats['meditation']}")
    logger.debug(f"Processed journal stats: {journal_stats}")
    logger.debug(f"Processed meditation stats: {meditation_stats}")
    
    
    # Check for pending therapist requests
    pending_requests = db.get_pending_requests_for_user(user_id)
    has_pending = len(pending_requests) > 0
    
    stats_col1, stats_col2, stats_col3 = st.columns(3)
    
    with stats_col1:
        st.markdown(f"""
            <div style="background-color:#ffffff;padding:15px;border-radius:10px;box-shadow:0 4px 6px rgba(0,0,0,0.1)">
                <h3 style="color:#576574;margin:0;">Journal Entries</h3>
                <p style="color:#2e86de;font-size:32px;font-weight:bold;margin:0;">{journal_stats.get('total_entries', 0)}</p>
                {f'<span style="position:absolute;top:-5px;right:-5px;background-color:#ff6b6b;color:white;border-radius:50%;width:20px;height:20px;display:flex;align-items:center;justify-content:center;font-size:12px;">{len(pending_requests)}</span>' if has_pending else ''}
            </div>
        """, unsafe_allow_html=True)
    
    with stats_col2:
        st.markdown(f"""
            <div style="background-color:#ffffff;padding:15px;border-radius:10px;box-shadow:0 4px 6px rgba(0,0,0,0.1)">
                <h3 style="color:#576574;margin:0;">Avg Mood</h3>
                <p style="color:#2e86de;font-size:32px;font-weight:bold;margin:0;">{journal_stats.get('avg_mood', 0):.1f}</p>
            </div>
        """, unsafe_allow_html=True)
    
    with stats_col3:
        st.markdown(f"""
            <div style="background-color:#ffffff;padding:15px;border-radius:10px;box-shadow:0 4px 6px rgba(0,0,0,0.1)">
                <h3 style="color:#576574;margin:0;">Meditation Minutes</h3>
                <p style="color:#2e86de;font-size:32px;font-weight:bold;margin:0;">{meditation_stats['total_minutes']}</p>
            </div>
        """, unsafe_allow_html=True)

def show_recent_activity(user_id: str):
    """Display recent activity section"""
    st.subheader("Recent Activity")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT entry_type as type, 
                       timestamp as time,
                       substr(content, 1, 50) as preview
                FROM journal_entries
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 3
            """, (user_id,))
            activities = cursor.fetchall()
            
        if not activities:
            st.info("No recent journal entries found")
            return
            
        for activity in activities:
            icon = "📔" if activity["type"] == "journal" else "🧘"
            # Handle all possible timestamp formats from SQLite
            timestamp_str = activity["time"]
            try:
                # Try ISO format first (handles most cases)
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except ValueError:
                try:
                    # Try with microseconds
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
                except ValueError:
                    try:
                        # Try without microseconds
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError as e:
                        logger.error(f"Failed to parse timestamp '{timestamp_str}': {str(e)}")
                        timestamp = datetime.now()  # Fallback to current time
            
            # Ensure both datetimes are timezone-aware
            now = datetime.now().astimezone()
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=now.tzinfo)
            time_diff = now - timestamp
            if time_diff.days > 0:
                time_str = f"{time_diff.days} days ago"
            else:
                hours = time_diff.seconds // 3600
                time_str = f"{hours} hours ago" if hours > 0 else "Less than an hour ago"
            st.markdown(f"""
            <div style="background-color:#ffffff;padding:15px;border-radius:10px;box-shadow:0 2px 4px rgba(0,0,0,0.05);margin-bottom:10px">
                <div style="display:flex;align-items:center">
                    <span style="font-size:24px;margin-right:15px">{icon}</span>
                    <div>
                        <p style="color:#576574;margin:0;font-weight:bold">{activity["type"].title()} • {time_str}</p>
                        <p style="color:#8395a7;margin:0">{activity["preview"]}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Error fetching recent activity: {str(e)}")
        st.error("Failed to load recent activity")

def show_daily_prompt():
    """Display daily mental wellness prompt"""
    prompts = [
        "Take 5 deep breaths and notice how you feel",
        "Write down three things you're grateful for today",
        "Notice any tension in your body and gently release it",
        "Reflect on a recent challenge and what you learned",
        "Practice mindful eating during your next meal"
    ]
    
    today_prompt = prompts[datetime.now().day % len(prompts)]
    
    st.markdown(f"""
        <div style="background-color:#f8f9fa;padding:20px;border-radius:10px;margin-top:20px">
            <h3 style="color:#2e86de;margin-top:0;">Today's Wellness Prompt</h3>
            <p style="color:#576574;font-size:18px;">{today_prompt}</p>
            <button style="background-color:#2e86de;color:white;border:none;padding:8px 16px;border-radius:5px;cursor:pointer;">
                I did this
            </button>
        </div>
    """, unsafe_allow_html=True)

def show(user_id):
    """Main home page function that matches the expected interface"""
    try:
        show_welcome_banner()
        with st.spinner('Loading latest stats...'):
            show_quick_stats(user_id)
        
        st.markdown("---")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            display_visualizations(user_id)  # Pass the user_id to get proper visualizations
        
        with col2:
            show_recent_activity(user_id)
            show_daily_prompt()
            
    except Exception as e:
        logger.error(f"Error displaying home page: {str(e)}")
        st.error("An error occurred while loading the dashboard")
