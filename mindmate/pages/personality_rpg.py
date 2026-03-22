import streamlit as st
from datetime import datetime
from ..utils.database import get_db_connection
from ..utils.visualization import render_skill_tree

class PersonalityRPG:
    def __init__(self, user_id=None):
        """Initialize RPG system with user authentication check"""
        self.db = get_db_connection()
        self.user_id = user_id or st.session_state.get('user_id')
        if not self.user_id:
            st.error("Please login to access the RPG features")
        
    def create_character(self):
        """Handle character creation with stats based on goals"""
        st.title("Create Your Hero")
        
        with st.form("character_form"):
            name = st.text_input("Hero Name")
            archetype = st.selectbox(
                "Choose Your Archetype",
                ["Warrior", "Mage", "Rogue", "Healer"]
            )
            
            # Base stats mapped to wellness goals
            stats = {
                "Resilience": st.slider("Resilience", 1, 10, 5),
                "Focus": st.slider("Focus", 1, 10, 5),
                "Creativity": st.slider("Creativity", 1, 10, 5),
                "Empathy": st.slider("Empathy", 1, 10, 5)
            }
            
            if st.form_submit_button("Begin Journey"):
                self._save_character(name, archetype, stats)
                return True
        return False

    def _save_character(self, name, archetype, stats):
        """Save character to database
        
        Args:
            name: Character name
            archetype: Character class/type
            stats: Dictionary of character stats
            
        Returns:
            bool: True if save succeeded, False otherwise
        """
        if not self.user_id:
            st.error("Authentication required. Please login first.")
            return False
            
        cursor = self.db.cursor()
        try:
            if not name or not archetype:
                raise ValueError("Character name and archetype are required")
            cursor.execute("""
                INSERT INTO rpg_characters 
                (user_id, name, archetype, stats, created_at)
                VALUES (?, ?, ?, ?, ?)
                """, 
                (self.user_id, name, archetype, str(stats), datetime.now())
            )
            self.db.commit()
            return True
        except Exception as e:
            st.error(f"Failed to save character: {str(e)}")
            return False

    def quest_system(self):
        """Display and track daily/weekly challenges"""
        st.title("Your Quests")
        
        # Sample quests mapped to wellness activities
        quests = [
            {"name": "Morning Meditation", "xp": 50, "type": "daily"},
            {"name": "Gratitude Journal", "xp": 30, "type": "daily"},
            {"name": "Sleep Routine", "xp": 100, "type": "weekly"}
        ]
        
        for quest in quests:
            cols = st.columns([3,1,1])
            cols[0].subheader(quest["name"])
            cols[1].write(f"{quest['xp']} XP")
            if cols[2].button("Complete", key=quest["name"]):
                self._complete_quest(quest)

    def _complete_quest(self, quest):
        """Record quest completion
        
        Args:
            quest: Dictionary containing quest details
            
        Raises:
            ValueError: If user is not authenticated or quest is invalid
        """
        if not self.user_id:
            st.error("Authentication required to complete quests")
            return
            
        if not quest or 'name' not in quest or 'xp' not in quest:
            raise ValueError("Invalid quest data")
            
        cursor = self.db.cursor()
        try:
            cursor.execute("""
            INSERT INTO rpg_quests 
            (user_id, quest_name, xp_earned, completed_at)
            VALUES (?, ?, ?, ?)
            """,
            (self.user_id, quest["name"], quest["xp"], datetime.now())
        )
            self.db.commit()
            st.success(f"Completed {quest['name']}! +{quest['xp']} XP")
            return True
        except Exception as e:
            st.error(f"Failed to complete quest: {str(e)}")
            return False


    def show_progression(self):
        """Display skill trees and achievements"""
        st.title("Your Progression")
        render_skill_tree(self.user_id)
        
        # Achievement badges display
        st.subheader("Achievements")
        # Implementation would query database for unlocked achievements

def show(user_id):
    rpg = PersonalityRPG(user_id=user_id)
    if 'character_created' not in st.session_state:
        if rpg.create_character():
            st.session_state.character_created = True
    else:
        rpg.quest_system()
        rpg.show_progression()
