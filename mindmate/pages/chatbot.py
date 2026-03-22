import streamlit as st
from groq import Groq
from mindmate.config import GROQ_API_KEY

if not GROQ_API_KEY:
    st.error("GROQ_API_KEY environment variable is not set. Please set it to your valid API key.")
    raise ValueError("GROQ_API_KEY environment variable is not set.")

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

# System prompt defining mental health assistant role
SYSTEM_PROMPT = """You are MindMate, an empathetic and supportive mental health companion. Your role is to:
- Provide emotional support and understanding
- Listen actively and respond with empathy
- Offer constructive coping strategies and suggestions
- Encourage professional help when appropriate
- Maintain a safe and non-judgmental space
- Never provide medical diagnosis or replace professional mental health care
- Always respond in a warm, supportive manner
- Analyze user's mood patterns and journal entries
- Suggest personalized activities based on their history
- Help identify patterns in their emotional state
- Provide gentle guidance and reflection prompts

Remember to:
1. Prioritize user safety and well-being
2. Reference their mood history when appropriate
3. Suggest activities tailored to their patterns
4. Help them reflect on their emotional journey"""

# Mental health resources
RESOURCES = [
    {"name": "Crisis Text Line", "url": "https://www.crisistextline.org/"},
    {"name": "National Suicide Prevention Lifeline", "url": "https://988lifeline.org/"},
    {"name": "NAMI Helpline", "url": "https://www.nami.org/help"},
    {"name": "Mental Health America", "url": "https://mhanational.org/"}
]

# Enhanced conversation starters with therapeutic prompts
CONVERSATION_STARTERS = [
    "I'm feeling anxious today - can you help me understand why?",
    "How can I improve my sleep quality?",
    "I'm struggling with motivation - any suggestions?",
    "What are some healthy ways to cope with stress?",
    "How do I know if I need professional help?",
    "Can you help me reflect on my recent mood patterns?",
    "What mindfulness exercises would you recommend?",
    "How can I build better emotional resilience?",
    "Can you suggest journal prompts for self-reflection?",
    "What activities might help improve my current mood?",
    "Can you recommend some mood-boosting activities?",
    "What creative outlets might help me express myself?",
    "How can I practice self-care today?",
    "What relaxation techniques would you suggest?",
    "How can I improve my morning routine?",
    "What are some ways to practice gratitude daily?"
]

def show(user_id: str):
    st.title("MindMate Therapeutic Chat")
    
    # Initialize StatsManager
    from mindmate.utils.stats_manager import StatsManager
    stats_manager = StatsManager(user_id)
    user_stats = stats_manager.get_all_stats()
    
    # Safety disclaimer
    with st.expander("Important Notice"):
        st.warning("""
        MindMate provides supportive conversations but is not a substitute for professional mental health care.
        If you're in crisis, please contact a licensed professional or emergency services immediately.
        """)
    
    # Enhanced mood tracker with history
    st.sidebar.subheader("Your Mood")
    mood = st.sidebar.select_slider(
        "How are you feeling today?",
        options=["😢 Very Low", "😞 Low", "😐 Neutral", "🙂 Good", "😊 Great"],
        value="😐 Neutral"
    )
    
    # Show mood history with visualization
    if user_stats['journal']:
        col1, col2 = st.sidebar.columns(2)
        col1.metric("Average Mood", f"{user_stats['journal'].get('avg_mood', 0):.1f}/10")
        col2.metric("Total Entries", user_stats['journal'].get('total_entries', 0))
        
        # Enhanced mood visualization
        with st.sidebar.expander("Mood Trend"):
            st.write("Your mood over time:")
            if len(user_stats['journal'].get('mood_history', [])) > 1:
                st.line_chart({
                    'Mood': user_stats['journal']['mood_history'],
                    '7-day Avg': user_stats['journal'].get('weekly_avg', [])
                }, height=150)
            else:
                st.info("Track more moods to see your trend")
    
    # Enhanced resources section with therapeutic tools
    with st.sidebar.expander("Resources & Tools"):
        st.subheader("Mental Health Resources")
        for resource in RESOURCES:
            st.markdown(f"[{resource['name']}]({resource['url']})")
        
        st.subheader("Therapeutic Tools")
        col1, col2 = st.columns(2)
        if col1.button("Mood Pattern Analysis"):
            if user_stats['journal']:
                avg_mood = user_stats['journal'].get('avg_mood', 0)
                st.session_state.messages.append({
                    "role": "user", 
                    "content": f"Analyze my mood patterns. My average mood is {avg_mood:.1f}/10"
                })
        
        if col2.button("Get Coping Strategies"):
            st.session_state.messages.append({
                "role": "user",
                "content": "Suggest personalized coping strategies based on my mood history"
            })
        
        st.subheader("Journal Insights")
        if st.button("Analyze Journal Entries"):
            st.session_state.messages.append({
                "role": "user",
                "content": "Analyze my recent journal entries for patterns and insights"
            })
        
        st.subheader("Activity Recommendations")
        cols = st.columns(2)
        if cols[0].button("Get Mood-Based Activities"):
            st.session_state.messages.append({
                "role": "user",
                "content": "Suggest personalized activities based on my current mood and history"
            })
        if cols[1].button("Quick Mood Boosters"):
            st.session_state.messages.append({
                "role": "user",
                "content": "Suggest 3 quick activities to improve my mood right now"
            })
    
    # Initialize chat history with user context
    if "messages" not in st.session_state:
        user_context = {
            "mood_history": f"Average mood: {user_stats['journal'].get('avg_mood', 0):.1f}" if user_stats['journal'] else "No mood history yet",
            "entry_count": user_stats['journal'].get('total_entries', 0) if user_stats['journal'] else 0,
            "meditation_minutes": user_stats['meditation'].get('total_minutes', 0) if user_stats['meditation'] else 0
        }
        context_prompt = f"{SYSTEM_PROMPT}\n\nUser Context:\n{user_context}"
        st.session_state.messages = [{"role": "system", "content": context_prompt}]
        st.session_state.mood = mood
        st.session_state.user_stats = user_stats

    # Conversation starters
    st.subheader("Need help getting started?")
    cols = st.columns(2)
    for i, starter in enumerate(CONVERSATION_STARTERS):
        if cols[i % 2].button(starter):
            st.session_state.messages.append({"role": "user", "content": starter})
            with st.chat_message("user"):
                st.markdown(starter)

    # Display chat messages (excluding system prompt)
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Enhanced chat input with mood and activity context
    chat_placeholder = f"How can I help you today? (Current mood: {mood})"
    if prompt := st.chat_input(chat_placeholder):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": f"Mood: {mood}\n{prompt}"})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response with therapeutic context
        try:
            therapeutic_context = {
                "current_mood": mood,
                "avg_mood": user_stats['journal'].get('avg_mood', 0) if user_stats['journal'] else None,
                "entry_count": user_stats['journal'].get('total_entries', 0) if user_stats['journal'] else 0
            }
            
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=st.session_state.messages,
                temperature=0.7,
                max_tokens=1000
            )
            ai_response = response.choices[0].message.content
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            with st.chat_message("assistant"):
                st.markdown(ai_response)

        except Exception as e:
            error_msg = str(e)
            if "Invalid API Key" in error_msg:
                st.error("Invalid API Key configuration. Please check your GROQ_API_KEY.")
            else:
                st.error("Sorry, I'm having trouble responding right now. Please try again later.")
            st.error(error_msg)
