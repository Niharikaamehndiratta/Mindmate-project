import streamlit as st
from datetime import datetime
import pandas as pd
import plotly.express as px
from mindmate.utils.database import get_db_connection
from mindmate.utils.mood_analysis import (
    analyze_mood_from_text,
    detect_keywords,
    get_mood_trends,
    get_mood_distribution,
    get_keyword_frequency
)

def show(user_id: str):
    """Main mood tracker page function"""
    st.title("😊 Mood Tracker")
    st.markdown("Track your emotional patterns and gain insights into your mental wellbeing")
    
    # Mood input section
    with st.expander("Log Your Mood"):
        col1, col2 = st.columns(2)
        with col1:
            mood_score = st.select_slider(
                "How are you feeling?",
                options=[1, 2, 3, 4, 5],
                value=3,
                format_func=lambda x: {
                    1: "😢 Terrible",
                    2: "😞 Sad", 
                    3: "😐 Neutral",
                    4: "🙂 Good",
                    5: "😁 Excellent"
                }[x]
            )
        with col2:
            notes = st.text_area("Optional notes about your mood")
            submitted = st.button("Save Mood Entry")
            
        if submitted:
            # Analyze mood from text notes if provided
            selected_mood = mood_score  # Save slider value
            keywords = []
            if notes:
                try:
                    # Convert slider value to -1 to 1 scale for averaging
                    slider_normalized = (selected_mood - 3) / 2
                    text_mood = analyze_mood_from_text(notes)
                    # Average the two scores and convert back to 1-5 scale
                    mood_score = ((slider_normalized + text_mood) / 2 * 2) + 3
                    keywords = detect_keywords(notes)
                except Exception as e:
                    st.error(f"Error analyzing mood: {str(e)}")
                    return
            
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO mood_entries 
                    (user_id, timestamp, mood_score, notes, tags) 
                    VALUES (?, ?, ?, ?, ?)""",
                    (user_id, datetime.now(), mood_score, notes, ",".join(keywords))
                )
                conn.commit()
                st.success("Mood entry saved successfully!")
            except Exception as e:
                st.error(f"Failed to save mood score entry: {str(e)}")
    
    # Mood history and analysis
    st.header("Your Mood History")
    try:
        conn = get_db_connection()
        mood_data = pd.read_sql(
            "SELECT id, user_id, timestamp, mood_score, notes, tags FROM mood_entries WHERE user_id = ? ORDER BY timestamp DESC", 
            conn,
            params=(user_id,)
        )
    
    except Exception as e:
        st.error(f"Error loading mood score data: {str(e)}")
        return
        
    if not mood_data.empty:
        # Use mood_score directly for analysis
        mood_data['mood_value'] = mood_data['mood_score']
        
        # Show interactive chart
        fig = px.line(
            mood_data,
            x='timestamp',
            y='mood_value',
            title='Your Mood Trend',
            labels={'mood_value': 'Mood Level', 'timestamp': 'Date'},
            height=400,
            template='plotly_white',
            line_shape='spline'
        )
        fig.update_traces(line=dict(width=3))
        fig.update_layout(hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)
        
        # Mood analysis
        st.header("Insights")
        
        # Show mood distribution
        dist_data = get_mood_distribution(user_id)
        st.subheader("Mood Distribution")
        dist_df = pd.DataFrame({
            "Mood": ["Positive", "Neutral", "Negative"],
            "Count": [dist_data["positive"], dist_data["neutral"], dist_data["negative"]]
        })
        fig = px.pie(
            dist_df,
            names="Mood",
            values="Count",
            color="Mood",
            color_discrete_map={
                "Positive": "green",
                "Neutral": "blue",
                "Negative": "red"
            }
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Show frequent keywords
        keywords = get_keyword_frequency(user_id, limit=10)
        if keywords:
            st.subheader("Frequent Mood Keywords")
            kw_df = pd.DataFrame(keywords)
            fig = px.bar(
                kw_df,
                x="keyword",
                y="count",
                labels={"keyword": "Keyword", "count": "Frequency"}
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No mood entries yet. Log your first mood above!")
