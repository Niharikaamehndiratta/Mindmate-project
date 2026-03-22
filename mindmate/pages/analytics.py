import streamlit as st
from mindmate.utils.database import get_db_connection
import pandas as pd
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def show_analytics(user_id):
    """Display comprehensive wellness analytics with interactive visualizations"""
    meditation_data = []
    mood_data = []
    sleep_data = []
    journal_data = []
    chatbot_data = []
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT DATE(timestamp) as date, 
                           session_type,
                           COUNT(*) as sessions,
                           SUM(minutes) as total_minutes,
                           AVG(minutes) as avg_minutes
                    FROM meditation_sessions 
                    WHERE user_id = ?
                    GROUP BY DATE(timestamp), session_type
                    ORDER BY date
                """, (user_id,))
                meditation_data = cursor.fetchall()
            except Exception as e:
                logger.error(f"Failed to fetch meditation data: {str(e)}")
                st.error(f"Failed to load meditation data: {type(e).__name__}: {str(e)}")
            
            try:
                cursor.execute("""
                    SELECT DATE(timestamp) as date,
                           AVG(mood_score) as avg_mood,
                           MIN(mood_score) as min_mood,
                           MAX(mood_score) as max_mood,
                           COUNT(*) as entries
                    FROM mood_entries
                    WHERE user_id = ?
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                """, (user_id,))
                mood_data = cursor.fetchall()
            except Exception as e:
                logger.error(f"Failed to fetch mood data: {str(e)}")
                st.error(f"Failed to load mood data: {type(e).__name__}: {str(e)}")
            
            try:
                cursor.execute("""
                    SELECT DATE(date) as date,
                           AVG(sleep_time) as avg_sleep,
                           AVG(sleep_quality) as avg_quality
                    FROM sleep_data
                    WHERE user_id = ?
                    GROUP BY DATE(date)
                    ORDER BY date
                """, (user_id,))
                sleep_data = cursor.fetchall()
            except Exception as e:
                logger.error(f"Failed to fetch sleep data: {str(e)}")
                st.error(f"Failed to load sleep data: {type(e).__name__}: {str(e)}")
            
            try:
                cursor.execute("""
                    SELECT DATE(timestamp) as date,
                           AVG(mood_score) as avg_mood,
                           COUNT(*) as entries
                    FROM journal_entries
                    WHERE user_id = ?
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                """, (user_id,))
                journal_data = cursor.fetchall()
            except Exception as e:
                logger.error(f"Failed to fetch journal data: {str(e)}")
                st.error(f"Failed to load journal data: {type(e).__name__}: {str(e)}")
            
            try:
                cursor.execute("""
                    SELECT DATE(timestamp) as date,
                           COUNT(*) as interactions,
                           AVG(response_helpful) as avg_helpfulness
                    FROM chatbot_sessions
                    WHERE user_id = ?
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                """, (user_id,))
                chatbot_data = cursor.fetchall()
            except Exception as e:
                logger.error(f"Failed to fetch chatbot data: {str(e)}")
                st.error(f"Failed to load chatbot data: {type(e).__name__}: {str(e)}")
            
        st.title("📊 Comprehensive Wellness Analytics")
        
        # Overall Wellness Score
        wellness_tab, meditation_tab, mood_tab, sleep_tab, journal_tab = st.tabs([
            "Overall Wellness", "Meditation Insights", "Mood Patterns", 
            "Sleep Quality", "Journal Analysis"
        ])
        
        with wellness_tab:
            st.subheader("Your Wellness Journey")
            
            # Combined wellness metrics
            if any([meditation_data, mood_data, sleep_data]):
                df_wellness = pd.DataFrame(meditation_data, 
                    columns=['date', 'type', 'sessions', 'minutes', 'avg_mins'])
                
                # Wellness Score Card
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Meditation Score", 
                        f"{sum(d[3] for d in meditation_data)/100:.1f}/10")
                with col2:
                    st.metric("Mood Score",
                        f"{sum(d[1] for d in mood_data)/len(mood_data):.1f}/5" 
                        if mood_data else "No data")
                with col3:
                    st.metric("Sleep Score",
                        f"{sum(d[2] for d in sleep_data)/len(sleep_data):.1f}/5"
                        if sleep_data else "No data")
                
                # Wellness Timeline
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    name='Meditation (mins)',
                    x=df_wellness['date'],
                    y=df_wellness['minutes'],
                    line=dict(color='blue')
                ))
                if mood_data:
                    df_mood = pd.DataFrame(mood_data, 
                        columns=['date', 'avg_mood', 'min_mood', 'max_mood', 'entries'])
                    fig.add_trace(go.Scatter(
                        name='Mood Score',
                        x=df_mood['date'],
                        y=df_mood['avg_mood'],
                        line=dict(color='green')
                    ))
                fig.update_layout(title='Your Wellness Timeline')
                st.plotly_chart(fig, use_container_width=True)
        
        with meditation_tab:
            st.subheader("Meditation Analysis")
            if meditation_data:
                df_med = pd.DataFrame(meditation_data, 
                    columns=['date', 'type', 'sessions', 'minutes', 'avg_mins'])
                
                # Session distribution
                fig = px.pie(df_med, values='sessions', names='type',
                    title='Meditation Type Distribution')
                st.plotly_chart(fig, use_container_width=True)
                
                # Time trend
                fig = px.line(df_med, x='date', y='minutes', color='type',
                    title='Meditation Minutes by Type Over Time')
                st.plotly_chart(fig, use_container_width=True)
        
        with mood_tab:
            st.subheader("Mood Patterns")
            if mood_data:
                df_mood = pd.DataFrame(mood_data,
                    columns=['date', 'avg_mood', 'min_mood', 'max_mood', 'entries'])
                
                # Mood range
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    name='Average Mood',
                    x=df_mood['date'],
                    y=df_mood['avg_mood'],
                    mode='lines',
                    line=dict(color='blue')
                ))
                fig.add_trace(go.Scatter(
                    name='Mood Range',
                    x=df_mood['date'],
                    y=df_mood['max_mood'],
                    mode='lines',
                    line=dict(width=0),
                    showlegend=False
                ))
                fig.add_trace(go.Scatter(
                    name='Mood Range',
                    x=df_mood['date'],
                    y=df_mood['min_mood'],
                    mode='lines',
                    fill='tonexty',
                    line=dict(width=0)
                ))
                fig.update_layout(title='Mood Range Over Time')
                st.plotly_chart(fig, use_container_width=True)
        
        with sleep_tab:
            st.subheader("Sleep Analysis")
            if sleep_data:
                df_sleep = pd.DataFrame(sleep_data,
                    columns=['date', 'avg_sleep', 'avg_quality'])
                
                # Sleep quality vs duration
                fig = px.scatter(df_sleep, x='avg_sleep', y='avg_quality',
                    title='Sleep Quality vs Duration',
                    labels={'avg_sleep': 'Sleep Duration (hours)',
                           'avg_quality': 'Sleep Quality Rating'})
                st.plotly_chart(fig, use_container_width=True)
        
        with journal_tab:
            st.subheader("Journal Insights")
            if journal_data:
                df_journal = pd.DataFrame(journal_data,
                    columns=['date', 'avg_mood', 'entries'])
                
                # Sentiment timeline
                fig = px.line(df_journal, x='date', y='avg_mood',
                    title='Journal Sentiment Over Time')
                fig.add_bar(x=df_journal['date'], y=df_journal['entries'],
                    name='Number of Entries')
                st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        logger.error(f"Failed to fetch analytics: {str(e)}")
        st.error(f"Failed to load analytics data: {str(e)}")

def show(user_id):
    """Main analytics page"""
    show_analytics(user_id)
