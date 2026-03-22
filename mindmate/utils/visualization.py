# Standard library imports
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Third-party imports
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt

# Local application imports
from mindmate.utils.mood_analysis import (
    get_mood_trends, 
    get_mood_distribution, 
    get_keyword_frequency,
    analyze_mood_from_text
)
from mindmate.utils.database import get_db_connection

# Constants
MOOD_KEYWORDS = {
    "positive": ["happy", "joy", "excited", "grateful", "peaceful", "content", "proud"],
    "negative": ["sad", "angry", "anxious", "stressed", "lonely", "tired", "overwhelmed"], 
    "neutral": ["okay", "fine", "normal", "average", "usual", "routine"]
}

logger = logging.getLogger(__name__)

def plot_mood_score_trend(mood_data: Dict, time_range: str = "week") -> Optional[go.Figure]:
    """Create an interactive line chart showing mood score trends with time range filtering"""
    try:
        if not mood_data.get("mood_trends"):
            return None

        df = pd.DataFrame(mood_data["mood_trends"])
        df['date'] = pd.to_datetime(df['date'])
        
        # Apply time range filter
        if time_range == "week":
            df = df[df['date'] >= datetime.now() - timedelta(days=7)]
        elif time_range == "month":
            df = df[df['date'] >= datetime.now() - timedelta(days=30)]
            
        # Create interactive figure with range selector
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['mood'],
            mode='lines+markers',
            name='Mood Score',
            line=dict(color='#3498db', width=2),
            marker=dict(size=6)
        ))
        
        # Add rolling average
        if len(df) > 7:
            df['rolling_avg'] = df['mood'].rolling(7).mean()
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['rolling_avg'],
                mode='lines',
                name='7-day Avg',
                line=dict(color='#e74c3c', width=2, dash='dot')
            ))
        
        # Customize layout
        fig.update_layout(
            xaxis_title='Date',
            yaxis_title='Mood Score',
            yaxis_range=[-1, 1],
            hovermode='x unified',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        # Add reference lines for mood ranges
        fig.add_hline(y=0.2, line_dash="dot", line_color="green", 
                     annotation_text="Positive Threshold", annotation_position="bottom right")
        fig.add_hline(y=-0.2, line_dash="dot", line_color="red", 
                     annotation_text="Negative Threshold", annotation_position="bottom right")
        
        return fig
        
    except Exception as e:
        logger.error(f"Failed to create mood trend chart: {str(e)}")
        return None

def plot_mood_score_distribution(mood_dist: Dict) -> Optional[go.Figure]:
    """Create an interactive donut chart showing mood score distribution with detailed breakdown"""
    try:
        if not mood_dist:
            return None

        labels = ['Positive', 'Neutral', 'Negative']
        values = [mood_dist['positive'], mood_dist['neutral'], mood_dist['negative']]
        colors = ['#2ecc71', '#f39c12', '#e74c3c']
        total = sum(values)
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker_colors=colors,
            hole=0.4,
            textinfo='percent+label+value',
            hoverinfo='label+percent+value',
            textposition='inside',
            textfont=dict(size=14)
        )])
        
        fig.update_traces(
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}",
            texttemplate="%{label}<br>%{value} (%{percent})"
        )
        
        fig.update_layout(
            title='Mood Distribution',
            showlegend=False,
            margin=dict(t=50, b=0, l=0, r=0)
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Failed to create mood distribution chart: {str(e)}")
        return None

def plot_keyword_frequency(keywords: List[Dict]) -> Optional[go.Figure]:
    """Create an interactive horizontal bar chart showing mood keyword frequency with sentiment coloring"""
    try:
        if not keywords:
            return None

        df = pd.DataFrame(keywords)
        
        # Classify keywords by sentiment
        df['sentiment'] = df['keyword'].apply(
            lambda x: 'positive' if x in MOOD_KEYWORDS['positive'] 
                     else 'negative' if x in MOOD_KEYWORDS['negative'] 
                     else 'neutral'
        )
        
        fig = px.bar(
            df.sort_values('count'),
            x='count',
            y='keyword',
            title='Most Frequent Mood Keywords',
            labels={'keyword': 'Keyword', 'count': 'Frequency'},
            color='sentiment',
            color_discrete_map={
                'positive': '#2ecc71',
                'neutral': '#f39c12',
                'negative': '#e74c3c'
            },
            orientation='h'
        )
        
        fig.update_layout(
            xaxis_title='Keyword',
            yaxis_title='Frequency',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            coloraxis_showscale=False
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Failed to create keyword frequency chart: {str(e)}")
        return None

def plot_activity_correlation(user_id: str) -> Optional[go.Figure]:
    """Create a heatmap showing correlation between different wellness activities and mood"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get combined data for correlation analysis
            cursor.execute("""
                SELECT 
                    j.timestamp as date,
                    j.mood_score,
                    m.minutes as meditation_minutes,
                    s.sleep_quality,
                    s.sleep_time
                FROM journal_entries j
                LEFT JOIN meditation_sessions m ON date(j.timestamp) = date(m.timestamp)
                LEFT JOIN sleep_data s ON date(j.timestamp) = date(s.date)
                WHERE j.user_id = ?
                GROUP BY date(j.timestamp)
            """, (user_id,))
            
            data = cursor.fetchall()
            
        if not data:
            return None
            
        df = pd.DataFrame(data)
        corr = df.corr()
        
        fig = px.imshow(
            corr,
            text_auto=True,
            aspect="auto",
            color_continuous_scale='RdBu',
            zmin=-1,
            zmax=1
        )
        
        fig.update_layout(
            title='Activity Correlation Matrix',
            xaxis_title='Metrics',
            yaxis_title='Metrics'
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Failed to create correlation heatmap: {str(e)}")
        return None

def plot_daily_mood_pattern(user_id: str) -> Optional[go.Figure]:
    """Create a line chart showing average mood by time of day"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    strftime('%H', timestamp) as hour,
                    AVG(mood_score) as avg_mood
                FROM journal_entries
                WHERE user_id = ?
                GROUP BY strftime('%H', timestamp)
                ORDER BY hour
            """, (user_id,))
            
            data = cursor.fetchall()
            
        if not data:
            return None
            
        df = pd.DataFrame(data)
        df['hour'] = df['hour'].astype(int)
        
        fig = px.line(
            df,
            x='hour',
            y='avg_mood',
            title='Daily Mood Pattern',
            labels={'hour': 'Hour of Day', 'avg_mood': 'Average Mood Score'},
            markers=True
        )
        
        fig.update_layout(
            xaxis=dict(
                tickmode='linear',
                tick0=0,
                dtick=1
            ),
            yaxis_range=[-1, 1]
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Failed to create daily mood pattern chart: {str(e)}")
        return None

def plot_meditation_progress(sessions_data: List[Dict]) -> Optional[go.Figure]:
    """Create an interactive bar chart showing meditation progress with goal tracking"""
    try:
        if not sessions_data:
            return None

        df = pd.DataFrame(sessions_data)
        df['date'] = pd.to_datetime(df['date'])
        
        fig = px.bar(
            df,
            x='date',
            y='minutes',
            title='Meditation Minutes Over Time',
            labels={'date': 'Date', 'minutes': 'Minutes'},
            color='minutes',
            color_continuous_scale='Greens'
        )
        
        fig.update_layout(
            xaxis_title='Date',
            yaxis_title='Minutes',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            coloraxis_showscale=False
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Failed to create meditation progress chart: {str(e)}")
        return None

def plot_wellness_timeline(user_id: str) -> Optional[go.Figure]:
    """Create a multi-metric timeline showing mood, meditation, and sleep together"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get combined wellness data
            cursor.execute("""
                SELECT 
                    date(j.timestamp) as date,
                    AVG(j.mood_score) as mood,
                    SUM(m.minutes) as meditation,
                    AVG(s.sleep_quality) as sleep_quality
                FROM journal_entries j
                LEFT JOIN meditation_sessions m ON date(j.timestamp) = date(m.timestamp)
                LEFT JOIN sleep_data s ON date(j.timestamp) = date(s.date)
                WHERE j.user_id = ?
                GROUP BY date(j.timestamp)
                ORDER BY date
            """, (user_id,))
            
            data = cursor.fetchall()
            
        if not data:
            return None
            
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        
        fig = go.Figure()
        
        # Add mood trace
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['mood'],
            name='Mood Score',
            line=dict(color='#3498db')
        ))
        
        # Add meditation trace
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['meditation'],
            name='Meditation (mins)',
            yaxis='y2',
            line=dict(color='#2ecc71')
        ))
        
        # Add sleep trace
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['sleep_quality'],
            name='Sleep Quality',
            yaxis='y3',
            line=dict(color='#9b59b6')
        ))
        
        fig.update_layout(
            title='Wellness Timeline',
            yaxis=dict(title='Mood Score', range=[-1, 1]),
            yaxis2=dict(
                title='Meditation (mins)',
                overlaying='y',
                side='right',
                range=[0, df['meditation'].max() * 1.1]
            ),
            yaxis3=dict(
                title='Sleep Quality',
                overlaying='y',
                side='left',
                anchor='free',
                position=0.15,
                range=[0, 5]
            ),
            hovermode='x unified'
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Failed to create wellness timeline: {str(e)}")
        return None

def display_visualizations(user_id: str = "default_user") -> None:
    """Display comprehensive wellness visualizations in Streamlit"""
    try:
        # Display mood visualizations
        display_mood_visualizations(user_id)
        
        # Add spacing
        st.markdown("---")
        
        # Meditation progress section
        st.subheader("Meditation Progress")
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    date(timestamp) as date,
                    SUM(minutes) as minutes
                FROM meditation_sessions
                WHERE user_id = ?
                GROUP BY date(timestamp)
                ORDER BY date
            """, (user_id,))
            meditation_data = [dict(row) for row in cursor.fetchall()]
        
        meditation_fig = plot_meditation_progress(meditation_data)
        if meditation_fig:
            st.plotly_chart(meditation_fig, use_container_width=True)
        else:
            st.info("No meditation data available yet")
        
        # Add spacing
        st.markdown("---")
        
        # Sleep quality section
        st.subheader("Sleep Patterns")
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    date,
                    sleep_quality,
                    sleep_time
                FROM sleep_data
                WHERE user_id = ?
                ORDER BY date
            """, (user_id,))
            sleep_data = [dict(row) for row in cursor.fetchall()]
        
        if sleep_data:
            sleep_df = pd.DataFrame(sleep_data)
            sleep_df['date'] = pd.to_datetime(sleep_df['date'])
            
            fig = px.line(
                sleep_df,
                x='date',
                y=['sleep_quality', 'sleep_time'],
                title='Sleep Quality and Duration',
                labels={'value': 'Score/Hours', 'variable': 'Metric'},
                color_discrete_map={
                    'sleep_quality': '#9b59b6',
                    'sleep_time': '#3498db'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No sleep data available yet")
        
        # Add spacing
        st.markdown("---")
        
        # Wellness correlation section
        st.subheader("Activity Correlations")
        corr_fig = plot_activity_correlation(user_id)
        if corr_fig:
            st.plotly_chart(corr_fig, use_container_width=True)
        else:
            st.info("Not enough data to show correlations yet")
        
        # Add spacing
        st.markdown("---")
        
        # Wellness timeline section
        st.subheader("Wellness Timeline")
        timeline_fig = plot_wellness_timeline(user_id)
        if timeline_fig:
            st.plotly_chart(timeline_fig, use_container_width=True)
        else:
            st.info("Not enough data to show timeline yet")
            
    except Exception as e:
        logger.error(f"Failed to display comprehensive visualizations: {str(e)}")
        st.error("An error occurred while generating visualizations")
    
def render_skill_tree(user_id: str) -> Optional[go.Figure]:
    """Create an interactive skill tree visualization for RPG character progression
    with branching paths and unlock indicators"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT stats FROM rpg_characters 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT 1
            """, (user_id,))
            result = cursor.fetchone()
            
        if not result:
            return None
            
        stats = eval(result[0])  # Convert string to dict
        archetypes = {
            "Warrior": ["Resilience", "Focus"],
            "Mage": ["Creativity", "Focus"],
            "Rogue": ["Creativity", "Empathy"],
            "Healer": ["Empathy", "Resilience"]
        }
        
        # Create enhanced skill tree with branches
        fig = go.Figure()
        
        # Main stats
        fig.add_trace(go.Scatterpolar(
            r=[stats.get(stat, 0) for stat in stats.keys()],
            theta=list(stats.keys()),
            fill='toself',
            name='Current Stats',
            marker=dict(
                size=12,
                color='#3498db',
                line=dict(width=2, color='DarkSlateGrey')
            )
        ))
        
        # Add branch connections
        for archetype, main_stats in archetypes.items():
            fig.add_trace(go.Scatterpolar(
                r=[stats.get(stat, 0) for stat in main_stats],
                theta=main_stats,
                mode='lines',
                line=dict(width=2, dash='dot'),
                name=f'{archetype} Path'
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 10],
                    tickvals=list(range(0, 11, 2))
                )),
            showlegend=True,
            title='Character Skill Tree',
            hovermode='closest',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Failed to render skill tree: {str(e)}")
        return None

def plot_achievements(user_id: str) -> Optional[go.Figure]:
    """Create achievement badges visualization showing unlocked accomplishments"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name, description, tier, unlocked_at 
                FROM rpg_achievements
                WHERE user_id = ?
                ORDER BY unlocked_at DESC
            """, (user_id,))
            achievements = [dict(row) for row in cursor.fetchall()]

        if not achievements:
            return None

        # Group by tier
        tiers = {
            'Bronze': [],
            'Silver': [],
            'Gold': []
        }
        for ach in achievements:
            tiers[ach['tier']].append(ach)

        # Create subplots for each tier
        fig = make_subplots(
            rows=1, 
            cols=3,
            subplot_titles=list(tiers.keys()),
            horizontal_spacing=0.1
        )

        # Add badges for each tier
        colors = {'Bronze': '#cd7f32', 'Silver': '#c0c0c0', 'Gold': '#ffd700'}
        for i, (tier, achievements) in enumerate(tiers.items(), 1):
            if achievements:
                fig.add_trace(
                    go.Scatter(
                        x=[1]*len(achievements),
                        y=[a['name'] for a in achievements],
                        mode='markers+text',
                        marker=dict(
                            size=20,
                            color=colors[tier],
                            symbol='circle'
                        ),
                        name=tier,
                        textposition='middle right',
                        hovertext=[a['description'] for a in achievements],
                        hoverinfo='text'
                    ),
                    row=1, col=i
                )

        fig.update_layout(
            title='Your Achievements',
            showlegend=False,
            margin=dict(t=100, b=20, l=20, r=20)
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Failed to create achievements visualization: {str(e)}")
        return None

def plot_level_progression(user_id: str) -> Optional[go.Figure]:
    """Create level progression visualization with XP bar"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT level, xp, xp_to_next_level 
                FROM rpg_progression
                WHERE user_id = ?
            """, (user_id,))
            result = cursor.fetchone()

        if not result:
            return None

        level, xp, xp_needed = result
        progress = min(100, (xp / xp_needed) * 100) if xp_needed > 0 else 0

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=progress,
            number={'suffix': '%'},
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': f"Level {level} Progress"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "#2ecc71"},
                'steps': [
                    {'range': [0, 50], 'color': "#e74c3c"},
                    {'range': [50, 80], 'color': "#f39c12"},
                    {'range': [80, 100], 'color': "#2ecc71"}
                ],
            }
        ))

        fig.update_layout(
            title=f"Level {level} - {xp}/{xp_needed} XP",
            margin=dict(t=50, b=20, l=20, r=20)
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Failed to create level progression visualization: {str(e)}")
        return None

def display_mood_visualizations(user_id: str = "default_user") -> None:
    """Display comprehensive mood and wellness visualizations in Streamlit"""
    try:
        st.header("Your Mental Wellness Insights")
        
        # Mood trends section
        st.subheader("Mood Trends")
        mood_trends = get_mood_trends(user_id)
        trend_fig = plot_mood_score_trend(mood_trends)
        if trend_fig:
            st.plotly_chart(trend_fig, use_container_width=True)
        else:
            st.info("No mood data available yet. Start journaling to see your trends!")
        
        # Mood distribution section
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Mood Distribution")
            mood_dist = get_mood_distribution(user_id)
            dist_fig = plot_mood_score_distribution(mood_dist)
            if dist_fig:
                st.plotly_chart(dist_fig, use_container_width=True)
            else:
                st.info("No mood distribution data available")
        
        # Keyword frequency section
        with col2:
            st.subheader("Common Mood Keywords")
            keywords = get_keyword_frequency(user_id)
            keyword_fig = plot_keyword_frequency(keywords)
            if keyword_fig:
                st.plotly_chart(keyword_fig, use_container_width=True)
            else:
                st.info("No keyword data available yet")
        
        # Add spacing
        st.markdown("---")
        
    except Exception as e:
        logger.error(f"Failed to display visualizations: {str(e)}")
        st.error("An error occurred while generating visualizations")
