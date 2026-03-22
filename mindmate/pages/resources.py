import streamlit as st
import logging

logger = logging.getLogger(__name__)

def show_resources_page():
    """Main resources page function"""
    try:
        st.title("Mental Health Resources")
        
        st.markdown("""
        ### Quick Access Resources
        - [National Suicide Prevention Lifeline](https://988lifeline.org): Call or text 988
        - [Crisis Text Line](https://www.crisistextline.org): Text HOME to 741741
        - [NAMI Helpline](https://www.nami.org/help): 1-800-950-NAMI (6264)
        """)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Self-Help Tools")
            st.markdown("""
            - [Mindful Breathing Exercise](https://www.mindful.org/daily-mindful-breathing-practice/)
            - [Anxiety Relief Techniques](https://www.helpguide.org/articles/anxiety/how-to-stop-worrying.htm)
            - [Sleep Hygiene Guide](https://www.sleepfoundation.org/sleep-hygiene)
            """)
            
        with col2:
            st.subheader("Professional Help")
            st.markdown("""
            - [Psychology Today Therapist Finder](https://www.psychologytoday.com/us/therapists)
            - [BetterHelp Online Therapy](https://www.betterhelp.com)
            - [Talkspace Online Counseling](https://www.talkspace.com)
            """)
            
        st.markdown("---")
        
        st.subheader("Daily Wellness Tip")
        st.info("Take 5 deep breaths when feeling stressed - inhale for 4 seconds, hold for 4, exhale for 6.")
        
    except Exception as e:
        logger.error(f"Error displaying resources page: {str(e)}")
        st.error("An error occurred while loading resources")
