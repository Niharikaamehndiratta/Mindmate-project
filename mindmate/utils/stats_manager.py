import logging
from datetime import datetime, timedelta
from mindmate.utils.database import get_journal_stats, get_meditation_stats
import streamlit as st

logger = logging.getLogger(__name__)

class StatsManager:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self._init_cache()

    def _init_cache(self):
        """Initialize stats cache in session state"""
        if 'stats_data' not in st.session_state:
            st.session_state.stats_data = {
                'last_updated': None,
                'journal': None,
                'meditation': None
            }

    def refresh_stats(self, force=False):
        """Refresh all stats from database"""
        if force or not st.session_state.stats_data['last_updated']:
            try:
                # Get fresh stats for both journal and meditation
                journal_stats = get_journal_stats(self.user_id)
                meditation_stats = get_meditation_stats(self.user_id)
                
                # Debug log the raw stats
                logger.debug(f"Raw journal stats: {journal_stats}")
                logger.debug(f"Raw meditation stats: {meditation_stats}")
                
                st.session_state.stats_data.update({
                    'journal': journal_stats if journal_stats else {'total_entries': 0, 'avg_mood': 0},
                    'meditation': meditation_stats if meditation_stats else {'total_minutes': 0},
                    'last_updated': datetime.now()
                })
                return True
            except Exception as e:
                logger.error(f"Error refreshing stats: {str(e)}")
                return False
        return False

    def get_journal_stats(self):
        """Get cached journal stats"""
        if not st.session_state.stats_data['journal']:
            self.refresh_stats(force=True)
        return st.session_state.stats_data['journal']

    def get_meditation_stats(self):
        """Get cached meditation stats"""
        if (not st.session_state.stats_data['meditation'] or 
            not st.session_state.stats_data['last_updated'] or
            (datetime.now() - st.session_state.stats_data['last_updated']) > timedelta(minutes=5)):
            self.refresh_stats(force=True)
        
        stats = st.session_state.stats_data['meditation']
        logger.debug(f"Returning meditation stats: {stats}")
        return stats

    def get_all_stats(self):
        """Get all stats in a single call"""
        # Force refresh if any stats are missing
        if not st.session_state.stats_data['journal'] or not st.session_state.stats_data['meditation']:
            self.refresh_stats(force=True)
            
        return {
            'journal': st.session_state.stats_data['journal'],
            'meditation': st.session_state.stats_data['meditation'],
            'last_updated': st.session_state.stats_data['last_updated']
        }
