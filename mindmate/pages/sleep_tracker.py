import streamlit as st
from datetime import datetime, time
import pandas as pd
import plotly.express as px
from utils.database import get_db_connection

def show(user_id: str):
    """Main sleep tracker page function"""
    st.title("😴 Sleep Tracker")
    st.markdown("Monitor your sleep patterns and improve your sleep quality")
    
    with st.expander("Log Sleep Data"):
        sleep_hours = st.number_input("Hours Slept", min_value=0.0, max_value=24.0, step=0.5, value=8.0)
        sleep_quality = st.slider("Sleep Quality (1-10)", 1, 10, 7)
        notes = st.text_area("Notes about your sleep")
        submitted = st.button("Save Sleep Data")
        
        if submitted:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO sleep_data 
                (user_id, date, sleep_time, sleep_quality, notes) 
                VALUES (?, ?, ?, ?, ?)""",
                (user_id,
                 datetime.now().date(), 
                 sleep_hours,
                 sleep_quality,
                 notes)
            )
            conn.commit()
            st.success("Sleep data saved successfully!")
    
    # Sleep history visualization
    st.header("Your Sleep Patterns")
    conn = get_db_connection()
    sleep_data = pd.read_sql(
        "SELECT * FROM sleep_data WHERE user_id = ? ORDER BY date DESC", 
        conn,
        params=(user_id,)
    )
    
    if not sleep_data.empty:
        # Convert date for plotting
        sleep_data['date'] = pd.to_datetime(sleep_data['date'])
        
        # Sleep Hours vs Quality scatter plot
        fig1 = px.scatter(
            sleep_data,
            x='sleep_time',
            y='sleep_quality',
            color='sleep_quality',
            title='Sleep Hours vs Quality',
            labels={'sleep_time': 'Hours Slept', 'sleep_quality': 'Sleep Quality'},
            height=400
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        # Sleep hours distribution
        fig2 = px.histogram(
            sleep_data,
            x='sleep_time',
            title='Sleep Hours Distribution',
            labels={'sleep_time': 'Hours Slept'},
            height=400
        )

        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No sleep data recorded yet. Log your first sleep above!")
