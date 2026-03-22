import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
from utils.database import get_db_connection

def show(user_id: str):
    """Main goals page function"""
    st.title("🎯 Wellness Goals")
    st.markdown("Set and track your mental wellness goals")
    
    # Goal creation section
    with st.expander("Create New Goal"):
        goal_name = st.text_input("Goal Name")
        goal_description = st.text_area("Description")
        goal_type = st.selectbox(
            "Goal Type",
            ["Mindfulness", "Exercise", "Sleep", "Social", "Learning", "Other"]
        )
        target_date = st.date_input(
            "Target Completion Date",
            min_value=datetime.today(),
            value=datetime.today() + timedelta(days=7)
        )
        target_value = st.number_input("Target Value (e.g., minutes per day, days per week)", min_value=1)
        
        if st.button("Save Goal"):
            if goal_name:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO goals 
                    (user_id, name, description, type, created_date, target_date, target_value, progress) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (user_id, goal_name, goal_description, goal_type, 
                     datetime.now(), target_date, target_value, 0)
                )
                conn.commit()
                st.success("Goal saved successfully!")
            else:
                st.warning("Please enter a goal name")
    
    # Active goals section
    st.header("Your Active Goals")
    conn = get_db_connection()
    goals_data = pd.read_sql(
        "SELECT * FROM goals WHERE user_id = ? AND completed = 0 ORDER BY target_date ASC", 
        conn,
        params=(user_id,)
    )
    
    if not goals_data.empty:
        # Calculate days remaining and completion percentage
        goals_data['days_remaining'] = (
            pd.to_datetime(goals_data['target_date']) - datetime.now()
        ).dt.days
        goals_data['completion_pct'] = (goals_data['progress'] / goals_data['target_value']) * 100
        
        # Display goals with progress
        for _, goal in goals_data.iterrows():
            with st.container():
                col1, col2 = st.columns([3,1])
                with col1:
                    st.subheader(goal['name'])
                    st.caption(f"Type: {goal['type']} | Target: {goal['target_value']} | Due in {goal['days_remaining']} days")
                    st.progress(min(100, int(goal['completion_pct'])))
                with col2:
                    progress = st.number_input(
                        "Update Progress",
                        min_value=0,
                        max_value=goal['target_value'],
                        value=goal['progress'],
                        key=f"progress_{goal['id']}"
                    )
                    if st.button("Save", key=f"save_{goal['id']}"):
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE goals SET progress = ? WHERE id = ?",
                            (progress, goal['id'])
                        )
                        if progress >= goal['target_value']:
                            cursor.execute(
                                "UPDATE goals SET completed = 1 WHERE id = ?",
                                (goal['id'],)
                            )
                        conn.commit()
                        st.experimental_rerun()
        
        # Goals visualization
        st.header("Goals Overview")
        fig = px.bar(
            goals_data,
            x='name',
            y='completion_pct',
            color='type',
            title='Goal Completion Progress',
            labels={'name': 'Goal', 'completion_pct': 'Completion %'},
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No active goals. Create your first goal above!")
