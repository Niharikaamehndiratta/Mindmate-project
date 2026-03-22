import streamlit as st
import time
from mindmate.utils import animations

def show(user_id):
    st.title("🌬️ Breathing Exercises")
    st.markdown("### Relax and center yourself with guided breathing")
    
    exercise = st.radio(
        "Choose an exercise:",
        ["Box Breathing", "4-7-8 Technique", "Deep Breathing"]
    )
    
    duration = st.slider("Duration (minutes)", 1, 10, 3)
    
    if st.button("Start Exercise"):
        st.markdown("---")
        placeholder = st.empty()
        progress_bar = st.progress(0)
        
        if exercise == "Box Breathing":
            guide = "Breathe in for 4, hold for 4, out for 4, hold for 4"
            cycle = [("Breathe IN", 4), ("Hold", 4), ("Breathe OUT", 4), ("Hold", 4)]
        elif exercise == "4-7-8 Technique":
            guide = "Breathe in for 4, hold for 7, out for 8"
            cycle = [("Breathe IN", 4), ("Hold", 7), ("Breathe OUT", 8)]
        else:  # Deep Breathing
            guide = "Slow deep breaths in and out"
            cycle = [("Breathe IN", 5), ("Breathe OUT", 5)]
        
        st.info(f"💡 {guide}")
        
        total_seconds = duration * 60
        start_time = time.time()
        
        while (time.time() - start_time) < total_seconds:
            for phase, seconds in cycle:
                for i in range(seconds, 0, -1):
                    placeholder.markdown(f"## {phase}\n### {i}")
                    progress = 1 - ((time.time() - start_time) / total_seconds)
                    progress_bar.progress(progress)
                    time.sleep(1)
        
        placeholder.success("✅ Exercise complete!")
        progress_bar.empty()
        animations.confetti()
