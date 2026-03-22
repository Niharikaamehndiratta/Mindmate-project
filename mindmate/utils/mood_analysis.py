import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import re
from collections import defaultdict
from textblob import TextBlob
from mindmate.utils.database import get_db_connection

logger = logging.getLogger(__name__)

MOOD_KEYWORDS = {
    "positive": ["happy", "joy", "excited", "grateful", "peaceful", "content", "proud"],
    "negative": ["sad", "angry", "anxious", "stressed", "lonely", "tired", "overwhelmed"],
    "neutral": ["okay", "fine", "normal", "average", "usual", "routine"]
}

def analyze_mood_from_text(text: str) -> float:
    """
    Analyze mood from journal text using sentiment analysis.
    Returns a score between -1 (very negative) to 1 (very positive).
    """
    try:
        analysis = TextBlob(text)
        return analysis.sentiment.polarity
    except Exception as e:
        logger.error(f"Failed to analyze mood from text: {str(e)}")
        return 0.0

def detect_keywords(text: str) -> List[str]:
    """Detect mood-related keywords in journal text"""
    found_keywords = []
    text_lower = text.lower()
    
    for mood_type, keywords in MOOD_KEYWORDS.items():
        for keyword in keywords:
            if re.search(rf"\b{keyword}\b", text_lower):
                found_keywords.append(keyword)
    
    return found_keywords

def get_mood_trends(user_id: str = "default_user", days: int = 30) -> Dict[str, List[Dict]]:
    """
    Get mood trends over time with daily averages.
    Returns data in format suitable for visualization.
    """
    try:
        with get_db_connection() as conn:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    date(timestamp) as day,
                    AVG(mood_score) as avg_mood,
                    COUNT(*) as entry_count
                FROM journal_entries
                WHERE user_id = ? AND date(timestamp) BETWEEN ? AND ?
                GROUP BY date(timestamp)
                ORDER BY day
            """, (user_id, start_date.date(), end_date.date()))
            
            results = cursor.fetchall()
            
            # Fill in missing days with null values
            date_range = [start_date + timedelta(days=i) for i in range(days + 1)]
            date_str_range = [date.strftime("%Y-%m-%d") for date in date_range]
            
            mood_data = []
            entry_counts = []
            
            # Create a dict of existing data for quick lookup
            existing_data = {row["day"]: row for row in results}
            
            for date_str in date_str_range:
                if date_str in existing_data:
                    row = existing_data[date_str]
                    mood_data.append({
                        "date": date_str,
                        "mood": round(row["avg_mood"], 2),
                        "entry_count": row["entry_count"]
                    })
                else:
                    mood_data.append({
                        "date": date_str,
                        "mood": None,
                        "entry_count": 0
                    })
            
            return {
                "mood_trends": mood_data,
                "time_range": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d")
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to get mood trends: {str(e)}")
        return {"mood_trends": [], "time_range": {}}

def get_mood_distribution(user_id: str = "default_user") -> Dict[str, int]:
    """Get distribution of mood scores (positive, neutral, negative)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Count positive moods (score > 0.2)
            cursor.execute("""
                SELECT COUNT(*) 
                FROM journal_entries 
                WHERE user_id = ? AND mood_score > 0.2
            """, (user_id,))
            positive = cursor.fetchone()[0]
            
            # Count neutral moods (-0.2 <= score <= 0.2)
            cursor.execute("""
                SELECT COUNT(*) 
                FROM journal_entries 
                WHERE user_id = ? AND mood_score BETWEEN -0.2 AND 0.2
            """, (user_id,))
            neutral = cursor.fetchone()[0]
            
            # Count negative moods (score < -0.2)
            cursor.execute("""
                SELECT COUNT(*) 
                FROM journal_entries 
                WHERE user_id = ? AND mood_score < -0.2
            """, (user_id,))
            negative = cursor.fetchone()[0]
            
            return {
                "positive": positive,
                "neutral": neutral,
                "negative": negative
            }
            
    except Exception as e:
        logger.error(f"Failed to get mood distribution: {str(e)}")
        return {"positive": 0, "neutral": 0, "negative": 0}

def get_keyword_frequency(user_id: str = "default_user", limit: int = 10) -> List[Dict]:
    """Get most frequent mood keywords from journal entries"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT keywords 
                FROM journal_entries 
                WHERE user_id = ? AND keywords IS NOT NULL
            """, (user_id,))
            
            keyword_counts = defaultdict(int)
            for row in cursor:
                if row["keywords"]:
                    for keyword in row["keywords"].split(","):
                        keyword_counts[keyword.strip()] += 1
            
            # Sort by frequency and limit results
            sorted_keywords = sorted(
                keyword_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:limit]
            
            return [{"keyword": k, "count": v} for k, v in sorted_keywords]
            
    except Exception as e:
        logger.error(f"Failed to get keyword frequency: {str(e)}")
        return []
