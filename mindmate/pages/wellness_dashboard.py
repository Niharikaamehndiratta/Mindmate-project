def show(user_id):
    """Display comprehensive wellness dashboard with metrics and visualizations"""
    import streamlit as st
    import pandas as pd
    import plotly.express as px
    from datetime import datetime, timedelta
    from mindmate.utils.database import get_user_data
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, Rectangle, Polygon, Ellipse
    import numpy as np
    
    st.title("🌱 Wellness Dashboard")

    # Get user data and calculate wellness score first
    mood_data, sleep_data, meditation_data = get_user_data(user_id)
    
    # Parse JSON data immediately after retrieval
    try:
        import json
        mood_data['history'] = json.loads(mood_data['history']) if mood_data['history'] else []
        sleep_data['history'] = json.loads(sleep_data['history']) if sleep_data['history'] else []
        mood_data['journal_entries'] = json.loads(mood_data['journal_entries']) if mood_data['journal_entries'] else []
    except json.JSONDecodeError as e:
        st.error(f"Error parsing data: {str(e)}")
        mood_data['history'] = []
        sleep_data['history'] = []
        mood_data['journal_entries'] = []
    
    wellness_score = calculate_wellness_score(mood_data, sleep_data, meditation_data)
    
    # Interactive Wellness Garden
    st.subheader("Your Wellness Garden")
    garden_fig, ax = plt.subplots(figsize=(10,5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis('off')
    
    # Garden elements grow based on wellness score
    wellness_level = min(wellness_score / 20, 5)  # Scale to 5 levels
    
    # Draw garden background
    ax.add_patch(Rectangle((0, 0), 10, 6, color='#87CEEB'))  # Sky
    ax.add_patch(Rectangle((1, 1), 8, 2, color='#8B4513'))  # Soil
    ax.add_patch(Rectangle((0, 1), 1, 2, color='#654321'))  # Fence
    ax.add_patch(Rectangle((9, 1), 1, 2, color='#654321'))  # Fence
    
    # Interactive garden elements
    for i in range(int(wellness_level)):
        flower_x = 2 + i * 1.5
        # Flower center with animation effect
        ax.add_patch(Circle((flower_x, 2.5), 0.3*(1+0.1*i), 
                          color=['#FFD700','#FFA500','#FF6347'][i%3]))
        for j in range(8):  # Petals
            angle = j * (360/8)
            x = flower_x + 0.5 * np.cos(np.radians(angle))
            y = 2.5 + 0.5 * np.sin(np.radians(angle))
            ax.add_patch(Circle((x, y), 0.2, color=['#FF69B4','#FFD700','#FF6347'][i%3]))
        ax.add_patch(Rectangle((flower_x-0.1, 1), 0.2, 1.5, color='green'))  # Stem
    
    # Weather effects based on mood
    if mood_data['average'] > 4:
        ax.add_patch(Circle((8, 4), 0.8, color='yellow'))  # Sun
    else:
        ax.add_patch(Circle((8, 4), 0.8, color='lightgray'))  # Cloud
        for i in range(5):  # Raindrops
            ax.plot([8 + i*0.3, 8 + i*0.3], [3.5, 3.2], color='blue', linewidth=1)

    # Tree grows based on meditation minutes
    if meditation_data['minutes'] > 0:
        tree_height = min(meditation_data['minutes'] / 20, 3)
        ax.add_patch(Rectangle((8.5, 1), 0.3, tree_height, color='#8B4513'))  # Trunk
        ax.add_patch(Polygon([[8.5,1+tree_height], [9.3,1+tree_height*0.7], [8.5,1+tree_height*0.4]], color='#228B22'))  # Leaves
    
    # Progress butterfly that moves based on score
    butterfly_x = min(9, 1 + wellness_score/12)
    ax.plot([butterfly_x, butterfly_x+0.3], [4, 4.2], color='black', linewidth=1)  # Antennae
    ax.add_patch(Ellipse((butterfly_x, 4), 0.8, 0.3, color='purple'))  # Body
    ax.add_patch(Polygon([[butterfly_x-0.4,4],[butterfly_x-0.2,4.3],[butterfly_x,4]], color='#FF69B4'))  # Wing
    ax.add_patch(Polygon([[butterfly_x+0.4,4],[butterfly_x+0.2,4.3],[butterfly_x,4]], color='#FF69B4'))  # Wing

    st.pyplot(garden_fig)
    st.caption("Your garden evolves with your wellness journey! The butterfly shows your progress.")
    
    st.metric("Your Wellness Score", f"{wellness_score}/100")
    
    # Metrics columns
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Avg Mood", f"{mood_data['average']:.1f}/5", 
                 f"{mood_data['change']:.1f} from last week")
    with col2:
        st.metric("Avg Sleep", f"{sleep_data['hours']} hours", 
                 f"{sleep_data['change']:.1f} hours")
    with col3:
        st.metric("Meditation", f"{meditation_data['sessions']} sessions", 
                 f"{meditation_data['minutes']} total mins")
    
    # Mood trend chart
    st.subheader("Mood Trends")
    try:
        mood_history = pd.DataFrame(mood_data['history'])
        if not mood_history.empty:
            mood_history['date'] = pd.to_datetime(mood_history['date'])
            mood_history = mood_history.sort_values('date')
        if not mood_history.empty:
            fig = px.line(mood_history, x='date', y='rating',
                         title="Your Mood Over Time")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No mood history data available yet")
    except Exception as e:
        st.warning("Could not display mood trends")
        st.error(f"Error: {str(e)}")
    
    # Sleep patterns
    st.subheader("Sleep Patterns")
    try:
        sleep_history = pd.DataFrame(sleep_data['history'])
        if not sleep_history.empty:
            sleep_history['date'] = pd.to_datetime(sleep_history['date'])
            sleep_history = sleep_history.sort_values('date')
        if not sleep_history.empty:
            fig = px.bar(sleep_history, x='date', y='hours',
                        title="Your Sleep Duration")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No sleep history data available yet")
    except Exception as e:
        st.warning("Could not display sleep patterns")
        st.error(f"Error: {str(e)}")
    
    # Journal insights
    st.subheader("Journal Insights")
    try:
        journal_entries = pd.DataFrame(mood_data['journal_entries'])
        if not journal_entries.empty:
            journal_entries['date'] = pd.to_datetime(journal_entries['date'])
            journal_entries = journal_entries.sort_values('date', ascending=False)
        if not journal_entries.empty:
            st.write("Recent journal highlights:")
            for _, entry in journal_entries.head(3).iterrows():
                st.markdown(f"- {entry['date']}: {entry['text'][:100]}...")
        else:
            st.info("No journal entries yet. Try writing in your journal!")
    except Exception as e:
        st.warning("Could not display journal insights")
        st.error(f"Error: {str(e)}")
    
    # Recommendations
    st.subheader("Personalized Recommendations")
    if wellness_score < 60:
        st.warning("Your wellness score is low. Consider:")
        st.markdown("- More consistent sleep schedule")
        st.markdown("- Daily meditation practice")
        st.markdown("- Journaling to process emotions")
    else:
        st.success("Great job! Keep up your wellness habits.")

def calculate_wellness_score(mood, sleep, meditation):
    """Calculate composite wellness score from metrics"""
    mood_score = mood['average'] * 20  # Scale 1-5 to 20-100
    sleep_score = min(sleep['hours'] * 10, 100)  # 10 hours = perfect score
    meditation_score = min(meditation['minutes'], 100)  # 100 mins = perfect score
    return int((mood_score * 0.5 + sleep_score * 0.3 + meditation_score * 0.2))
