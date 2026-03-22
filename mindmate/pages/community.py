import streamlit as st
import pandas as pd
from datetime import datetime
from utils.database import get_db_connection

def show_community_page():
    st.title("🤝 Community Support")
    st.markdown("Connect with others on their mental wellness journey")
    
    # Wellness dashboard announcement
    with st.container():
        st.subheader("✨ Coming Soon")
        st.info("""
        Our new **community support** feature will be launching soon!
        Track and visualize your mental health progress with interactive charts
        and personalized insights.
        """)
    
    # Community posts section
    st.header("Community Discussions")
    
    # Create new post
    with st.expander("Create New Post"):
        post_title = st.text_input("Title")
        post_content = st.text_area("Content")
        post_category = st.selectbox(
            "Category",
            ["General", "Support", "Success Story", "Question", "Resource Share"]
        )
        
        if st.button("Post"):
            if post_title and post_content:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO community_posts 
                    (title, content, category, author, created_at, likes) 
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (post_title, post_content, post_category, 
                     "Current User", datetime.now(), 0)
                )
                conn.commit()
                st.success("Post created successfully!")
            else:
                st.warning("Please enter both title and content")
    
    # View posts
    conn = get_db_connection()
    posts = pd.read_sql(
        "SELECT * FROM community_posts ORDER BY created_at DESC LIMIT 20", 
        conn
    )
    
    if not posts.empty:
        for _, post in posts.iterrows():
            with st.container():
                st.subheader(post['title'])
                st.caption(f"Posted by {post['author']} | {post['created_at']} | Category: {post['category']}")
                st.write(post['content'])
                
                col1, col2 = st.columns([1, 10])
                with col1:
                    if st.button(f"❤️ {post['likes']}", key=f"like_{post['id']}"):
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE community_posts SET likes = likes + 1 WHERE id = ?",
                            (post['id'],)
                        )
                        conn.commit()
                        st.experimental_rerun()
                with col2:
                    if st.button("💬 Comment", key=f"comment_{post['id']}"):
                        with st.expander("Add Comment"):
                            comment = st.text_area("Your Comment")
                            if st.button("Post Comment"):
                                if comment:
                                    cursor = conn.cursor()
                                    cursor.execute(
                                        """INSERT INTO community_comments 
                                        (post_id, author, content, created_at) 
                                        VALUES (?, ?, ?, ?)""",
                                        (post['id'], "Current User", comment, datetime.now())
                                    )
                                    conn.commit()
                                    st.success("Comment added!")
                                else:
                                    st.warning("Please enter a comment")
                
                # Show comments if any
                comments = pd.read_sql(
                    f"SELECT * FROM community_comments WHERE post_id = {post['id']} ORDER BY created_at",
                    conn
                )
                if not comments.empty:
                    with st.expander(f"View Comments ({len(comments)})"):
                        for _, comment in comments.iterrows():
                            st.caption(f"{comment['author']} - {comment['created_at']}")
                            st.write(comment['content'])
                
                st.divider()
    else:
        st.info("No posts yet. Be the first to share!")
    
    # Support groups section
    st.header("Support Groups")
    groups = [
        {"name": "Anxiety Support", "members": 245, "meeting": "Every Tuesday 7pm"},
        {"name": "Depression Recovery", "members": 189, "meeting": "Every Thursday 6pm"},
        {"name": "Mindfulness Practitioners", "members": 312, "meeting": "Daily 8am"},
        {"name": "Parenting & Mental Health", "members": 156, "meeting": "Every Sunday 4pm"}
    ]
    
    for group in groups:
        with st.expander(f"{group['name']} ({group['members']} members)"):
            st.write(f"**Next meeting:** {group['meeting']}")
            if st.button("Join Group", key=f"join_{group['name']}"):
                st.success(f"You've joined {group['name']}!")

if __name__ == "__main__":
    show_community_page()
