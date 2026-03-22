import streamlit as st
from datetime import datetime, timedelta
import time
from mindmate.utils import animations

def show(user_id):
    st.title("🍅 Productivity Timer")
    st.markdown("### Pomodoro-style focus sessions")
    
    # Timer settings
    col1, col2 = st.columns(2)
    with col1:
        work_min = st.number_input("Work duration (minutes)", min_value=1, max_value=120, value=25)
    with col2:
        break_min = st.number_input("Break duration (minutes)", min_value=1, max_value=30, value=5)
    
    # Timer display
    timer_placeholder = st.empty()
    status_placeholder = st.empty()
    
    # Control buttons
    start_button = st.button("Start Session")
    stop_button = st.button("Stop")
    
    if start_button:
        work_seconds = work_min * 60
        break_seconds = break_min * 60
        
        # Work phase
        status_placeholder.success("⏳ Focus time! Work on your task")
        for i in range(work_seconds, 0, -1):
            mins, secs = divmod(i, 60)
            timer_placeholder.markdown(f"### {mins:02d}:{secs:02d}")
            time.sleep(1)
            
        # Break phase
        status_placeholder.success("☕ Break time! Relax and recharge")
        for i in range(break_seconds, 0, -1):
            mins, secs = divmod(i, 60)
            timer_placeholder.markdown(f"### {mins:02d}:{secs:02d}")
            time.sleep(1)
            
        status_placeholder.success("✅ Session complete!")
        animations.confetti()
        
    if stop_button:
        timer_placeholder.empty()
        status_placeholder.info("Timer stopped")
