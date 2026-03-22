from datetime import datetime, time, timedelta
from typing import Dict, List, Optional
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson import ObjectId

def get_collection(collection_name: str):
    """Get MongoDB collection instance"""
    client = MongoClient('mongodb://localhost:27017/')
    db = client['mindmate']
    return db[collection_name]

# User Profile Functions
def get_user_profile(user_id: str) -> Optional[Dict]:
    """Get user profile by ID
    
    Args:
        user_id: User ID as string or ObjectId
        
    Returns:
        User profile dict if found, None otherwise
    """
    users_collection = get_collection('users')
    try:
        # Try querying with string ID first
        profile = users_collection.find_one({'_id': user_id})
        if profile:
            return profile
            
        # If not found, try converting to ObjectId
        try:
            from bson import ObjectId
            return users_collection.find_one({'_id': ObjectId(user_id)})
        except:
            return None
            
    except Exception as e:
        return None

def update_user_profile(user_id: str, updates: Dict) -> None:
    """Update user profile"""
    users_collection = get_collection('users')
    users_collection.update_one(
        {'_id': user_id},
        {'$set': updates}
    )

def get_client_info(client_id: str) -> Dict:
    """Get comprehensive client information including profile, sessions, and activity
    
    Args:
        client_id: ID of the client to get info for
        
    Returns:
        Dictionary containing:
        - profile: Basic user profile
        - sessions: List of session notes
        - mood_history: Recent mood entries
        - activity: Recent activity
        - stats: Various client statistics
    """
    try:
        profile = get_user_profile(client_id)
        if not profile:
            raise ValueError(f"Client {client_id} not found")
            
        return {
            'profile': profile,
            'sessions': list(get_collection('session_notes').find(
                {'client_id': client_id},
                sort=[('date', -1)],
                limit=10
            )),
            'mood_history': get_mood_history(client_id, limit=7),
            'activity': get_recent_activity(client_id, limit=10),
            'stats': {
                'session_count': profile.get('session_count', 0),
                'unread_messages': get_unread_count(client_id),
                'journal_entries': get_journal_stats(client_id).get('entries_count', 0)
            }
        }
    except Exception as e:
        raise ValueError(f"Error getting client info: {str(e)}")

# Messaging Functions
def save_message(sender_id: str, recipient_id: str, content: str) -> None:
    """Save a message between users"""
    messages_collection = get_collection('messages')
    messages_collection.insert_one({
        'sender_id': sender_id,
        'recipient_id': recipient_id,
        'content': content,
        'timestamp': datetime.now(),
        'read': False
    })

def get_messages(user_id: str, other_user_id: str, limit: int = 50, sort_asc: bool = False) -> List[Dict]:
    """Get message history between two users with sorting control
    
    Args:
        user_id: ID of first user
        other_user_id: ID of second user
        limit: Maximum number of messages to return
        sort_asc: If True, sort by oldest first; if False, newest first
        
    Returns:
        List of message dictionaries
    """
    messages_collection = get_collection('messages')
    sort_order = 1 if sort_asc else -1
    return list(messages_collection.find({
        '$or': [
            {'sender_id': user_id, 'recipient_id': other_user_id},
            {'sender_id': other_user_id, 'recipient_id': user_id}
        ]
    }).sort('timestamp', sort_order).limit(limit))

def get_therapist_client_messages(therapist_id: str, client_id: str, limit: int = 50) -> List[Dict]:
    """Get messages between therapist and client
    
    Args:
        therapist_id: ID of therapist
        client_id: ID of client
        limit: Maximum number of messages to return
        
    Returns:
        List of message dictionaries sorted by timestamp ascending
    """
    # Verify therapist-client relationship
    relationships_collection = get_collection('therapist_client_relationships')
    relationship = relationships_collection.find_one({
        'therapist_id': therapist_id,
        'client_id': client_id,
        'active': True
    })
    
    if not relationship:
        raise ValueError("No active therapist-client relationship found")
        
    return get_messages(therapist_id, client_id, limit, sort_asc=True)

def verify_therapist_client_relationship(therapist_id: str, client_id: str) -> bool:
    """Verify if there's an active therapist-client relationship
    
    Args:
        therapist_id: ID of therapist
        client_id: ID of client
        
    Returns:
        bool: True if relationship exists and is active
    """
    relationships_collection = get_collection('therapist_client_relationships')
    relationship = relationships_collection.find_one({
        'therapist_id': therapist_id,
        'client_id': client_id,
        'active': True
    })
    return bool(relationship)

def get_unread_messages_count(user_id: str, other_user_id: str) -> int:
    """Get count of unread messages from specific sender
    
    Args:
        user_id: ID of recipient
        other_user_id: ID of sender
        
    Returns:
        int: Number of unread messages
    """
    messages_collection = get_collection('messages')
    return messages_collection.count_documents({
        'sender_id': other_user_id,
        'recipient_id': user_id,
        'read': False
    })

def add_reaction(message_id: str, reaction: str) -> None:
    """Add reaction to a message"""
    messages_collection = get_collection('messages')
    messages_collection.update_one(
        {'_id': message_id},
        {'$set': {'reaction': reaction}}
    )

def get_reactions(user_id: str) -> List[Dict]:
    """Get all reactions for a user's messages"""
    messages_collection = get_collection('messages')
    return list(messages_collection.find({
        'recipient_id': user_id,
        'reaction': {'$exists': True}
    }))

def get_unread_count(user_id: str) -> int:
    """Count unread messages for a user"""
    messages_collection = get_collection('messages')
    return messages_collection.count_documents({
        'recipient_id': user_id,
        'read': False
    })

def mark_messages_read(user_id: str, sender_id: str) -> None:
    """Mark messages from a sender as read"""
    messages_collection = get_collection('messages')
    messages_collection.update_many({
        'sender_id': sender_id,
        'recipient_id': user_id,
        'read': False
    }, {'$set': {'read': True}})

# Therapist Functions
def is_user_therapist(user_id: str) -> bool:
    """Check if user is a therapist"""
    users_collection = get_collection('users')
    user = users_collection.find_one({'_id': user_id})
    return user.get('is_therapist', False) if user else False

def get_client_therapist(client_id: str) -> Optional[Dict]:
    """Get therapist assigned to a client"""
    relationships_collection = get_collection('therapist_client_relationships')
    relationship = relationships_collection.find_one({'client_id': client_id})
    if relationship:
        users_collection = get_collection('users')
        return users_collection.find_one({'_id': relationship['therapist_id']})
    return None

def get_therapist_by_credentials(email: str, password_hash: str) -> Optional[Dict]:
    """Authenticate therapist"""
    users_collection = get_collection('users')
    return users_collection.find_one({
        'email': email,
        'password_hash': password_hash,
        'is_therapist': True
    })

def get_therapist_profile(therapist_id: str) -> Optional[Dict]:
    """Get therapist profile by ID
    
    Args:
        therapist_id: ID of the therapist
        
    Returns:
        Dict: Therapist profile if found, None otherwise
    """
    users_collection = get_collection('users')
    return users_collection.find_one({'_id': therapist_id, 'is_therapist': True})

def get_therapist_id(email: str) -> Optional[str]:
    """Get therapist ID from email
    
    Args:
        email: Therapist's email address
        
    Returns:
        str: Therapist's ID if found, None otherwise
    """
    users_collection = get_collection('users')
    user = users_collection.find_one({'email': email, 'is_therapist': True})
    return str(user['_id']) if user else None

def get_therapist_clients(therapist_id: str, limit: int = 100, skip: int = 0) -> List[Dict]:
    """Get clients assigned to a therapist with pagination and enhanced data
    
    Args:
        therapist_id: ID of the therapist
        limit: Maximum number of clients to return (default: 100)
        skip: Number of clients to skip (for pagination)
        
    Returns:
        List of client dictionaries with enhanced fields
    """
    try:
        if not isinstance(therapist_id, ObjectId):
            therapist_id = ObjectId(therapist_id)
            
        relationships_collection = get_collection('therapist_client_relationships')
        users_collection = get_collection('users')
        
        # Get client IDs with pagination
        relationships = relationships_collection.find(
            {'therapist_id': therapist_id},
            {'client_id': 1, 'assigned_at': 1}
        ).skip(skip).limit(limit)
        
        client_data = []
        for rel in relationships:
            client_id = rel['client_id']
            try:
                # Handle both string and numeric client IDs
                client = users_collection.find_one({
                    '$or': [
                        {'_id': str(client_id)},
                        {'_id': client_id}
                    ]
                })
                if client:
                    # Get last session date
                    last_session = get_collection('session_notes').find_one(
                        {'client_id': client_id},
                        sort=[('date', -1)]
                    )
                    
                    client_data.append({
                        'id': str(client['_id']),
                        'name': client.get('username', 'Unknown'),
                        'email': client.get('email', ''),
                        'last_active': client.get('last_active', 'Never'),
                        'session_count': client.get('session_count', 0),
                        'last_note': client.get('last_note', ''),
                        'last_session': last_session['date'] if last_session else None,
                        'assigned_at': rel.get('assigned_at')
                    })
            except Exception as e:
                continue
                
        return client_data
        
    except Exception as e:
        raise ValueError(f"Error getting therapist clients: {str(e)}")

def assign_therapist(client_id: str, therapist_id: str, client_name: str = None, client_email: str = None) -> None:
    """Assign therapist to client with validation and duplicate checking
    
    Args:
        client_id: ID of client to assign
        therapist_id: ID of therapist to assign
        client_name: Optional client name for new user creation
        client_email: Optional client email for new user creation
        
    Raises:
        ValueError: If assignment fails validation
    """
    try:
        # Convert and validate IDs
        client_id_str = str(client_id)
        if not isinstance(therapist_id, ObjectId):
            therapist_id = ObjectId(therapist_id)
            
        relationships_collection = get_collection('therapist_client_relationships')
        users_collection = get_collection('users')
        
        # Create or update client user document
        client_data = {
            '_id': client_id_str,
            'username': client_name or f'Client {client_id_str}',
            'email': client_email or f'client{client_id_str}@example.com',
            'is_client': True,
            'created_at': datetime.now()
        }
        
        users_collection.update_one(
            {'_id': client_id_str},
            {'$set': client_data},
            upsert=True
        )
            
        # Check if therapist exists and is actually a therapist
        therapist = users_collection.find_one({'_id': therapist_id})
        if not therapist or not therapist.get('is_therapist'):
            raise ValueError("Therapist does not exist or is not a therapist")
            
        # Check for existing relationship
        existing = relationships_collection.find_one({
            'client_id': client_id_str,
            'therapist_id': therapist_id
        })
        if existing:
            raise ValueError("Therapist already assigned to this client")
            
        # Check therapist's client limit (max 50 clients)
        client_count = relationships_collection.count_documents({
            'therapist_id': therapist_id
        })
        if client_count >= 50:
            raise ValueError("Therapist has reached maximum client limit")
            
        # Create relationship
        relationships_collection.insert_one({
            'client_id': client_id_str,
            'therapist_id': therapist_id,
            'assigned_at': datetime.now(),
            'active': True
        })
        
    except Exception as e:
        raise ValueError(f"Failed to assign therapist: {str(e)}")

def remove_therapist_relationship(client_id: str, therapist_id: str) -> None:
    """Remove therapist-client relationship
    
    Args:
        client_id: ID of client
        therapist_id: ID of therapist
        
    Raises:
        ValueError: If removal fails
    """
    try:
        client_id_str = str(client_id)
        if not isinstance(therapist_id, ObjectId):
            therapist_id = ObjectId(therapist_id)
            
        relationships_collection = get_collection('therapist_client_relationships')
        result = relationships_collection.delete_one({
            'client_id': client_id_str,
            'therapist_id': therapist_id
        })
        
        if result.deleted_count == 0:
            raise ValueError("No matching relationship found")
            
    except Exception as e:
        raise ValueError(f"Failed to remove relationship: {str(e)}")

def get_client_count(therapist_id: str) -> int:
    """Get count of clients assigned to a therapist
    
    Args:
        therapist_id: ID of therapist
        
    Returns:
        Number of clients assigned
    """
    try:
        if not isinstance(therapist_id, ObjectId):
            therapist_id = ObjectId(therapist_id)
            
        relationships_collection = get_collection('therapist_client_relationships')
        return relationships_collection.count_documents({
            'therapist_id': therapist_id
        })
    except Exception as e:
        raise ValueError(f"Error getting client count: {str(e)}")

def get_therapist_analytics(therapist_id: str, time_period: str = "Last Month") -> Dict:
    """Get comprehensive analytics data for a therapist
    
    Args:
        therapist_id: ID of the therapist
        time_period: Time period for analytics ("Last Week", "Last Month", "Last 3 Months", "Last Year")
        
    Returns:
        Dictionary containing analytics data
    """
    try:
        if not isinstance(therapist_id, ObjectId):
            therapist_id = ObjectId(therapist_id)
            
        # Calculate date range
        now = datetime.now()
        if time_period == "Last Week":
            start_date = now - timedelta(days=7)
        elif time_period == "Last Month":
            start_date = now - timedelta(days=30)
        elif time_period == "Last 3 Months":
            start_date = now - timedelta(days=90)
        else:  # Last Year
            start_date = now - timedelta(days=365)
            
        # Get session data
        sessions = list(get_collection('session_notes').find({
            'therapist_id': therapist_id,
            'date': {'$gte': start_date}
        }))
        
        # Get attendance data
        attendance = {
            'attended': sum(1 for s in sessions if s.get('status') == 'attended'),
            'cancelled': sum(1 for s in sessions if s.get('status') == 'cancelled'),
            'no_show': sum(1 for s in sessions if s.get('status') == 'no_show')
        }
        
        # Get engagement metrics
        messages = list(get_collection('messages').find({
            '$or': [
                {'sender_id': therapist_id},
                {'recipient_id': therapist_id}
            ],
            'timestamp': {'$gte': start_date}
        }))
        
        return {
            'session_count': len(sessions),
            'attendance': attendance,
            'message_count': len(messages),
            'sessions': sessions,
            'messages': messages
        }
        
    except Exception as e:
        raise ValueError(f"Error getting therapist analytics: {str(e)}")

def get_treatment_milestones(therapist_id: str, client_id: str) -> List[Dict]:
    """Get treatment milestones for a specific client
    
    Args:
        therapist_id: ID of the therapist
        client_id: ID of the client
        
    Returns:
        List of milestone dictionaries
    """
    try:
        milestones_collection = get_collection('treatment_milestones')
        return list(milestones_collection.find({
            'therapist_id': ObjectId(therapist_id),
            'client_id': client_id
        }).sort('date', 1))
    except Exception as e:
        raise ValueError(f"Error getting treatment milestones: {str(e)}")

def save_treatment_milestone(therapist_id: str, client_id: str, milestone: Dict) -> None:
    """Save a treatment milestone
    
    Args:
        therapist_id: ID of the therapist
        client_id: ID of the client
        milestone: Dictionary containing milestone details
    """
    try:
        milestones_collection = get_collection('treatment_milestones')
        milestones_collection.insert_one({
            'therapist_id': ObjectId(therapist_id),
            'client_id': client_id,
            'date': milestone.get('date', datetime.now()),
            'event': milestone['event'],
            'notes': milestone.get('notes', ''),
            'created_at': datetime.now()
        })
    except Exception as e:
        raise ValueError(f"Error saving treatment milestone: {str(e)}")

# Session Notes
def save_session_note(therapist_id: str, client_id: str, note: str) -> None:
    """Save therapist's session notes"""
    notes_collection = get_collection('session_notes')
    notes_collection.insert_one({
        'therapist_id': therapist_id,
        'client_id': client_id,
        'note': note,
        'date': datetime.now()
    })

# Activity Tracking
def get_recent_activity(user_id: str, limit: int = 10) -> List[Dict]:
    """Get recent user activity"""
    activity_collection = get_collection('user_activity')
    return list(activity_collection.find(
        {'user_id': user_id},
        sort=[('timestamp', -1)],
        limit=limit
    ))

def get_client_activity(client_id: str) -> List[Dict]:
    """Get all activity for a client"""
    activity_collection = get_collection('user_activity')
    return list(activity_collection.find(
        {'user_id': client_id},
        sort=[('timestamp', -1)]
    ))

# Notifications
def log_notification(user_id: str, message: str, notification_type: str) -> None:
    """Log a notification for a user"""
    notifications_collection = get_collection('notifications')
    notifications_collection.insert_one({
        'user_id': user_id,
        'message': message,
        'type': notification_type,
        'timestamp': datetime.now(),
        'read': False
    })

def get_notification_history(user_id: str, limit: int = 20) -> List[Dict]:
    """Get notification history for a user"""
    notifications_collection = get_collection('notifications')
    return list(notifications_collection.find(
        {'user_id': user_id},
        sort=[('timestamp', -1)],
        limit=limit
    ))

def mark_notifications_read(user_id: str) -> None:
    """Mark all notifications as read for a user"""
    notifications_collection = get_collection('notifications')
    notifications_collection.update_many(
        {'user_id': user_id, 'read': False},
        {'$set': {'read': True}}
    )

def get_notification_settings(user_id: str) -> Dict:
    """Get notification settings for a user"""
    settings_collection = get_collection('notification_settings')
    settings = settings_collection.find_one({'user_id': user_id})
    return settings or {
        'email_notifications': True,
        'push_notifications': True,
        'message_notifications': True
    }

def save_notification_settings(user_id: str, settings: Dict) -> None:
    """Save notification settings for a user"""
    settings_collection = get_collection('notification_settings')
    settings_collection.update_one(
        {'user_id': user_id},
        {'$set': settings},
        upsert=True
    )

# Therapist Management
def get_available_therapists(specialization: str = None) -> List[Dict]:
    """Get list of available therapists"""
    users_collection = get_collection('users')
    query = {'is_therapist': True, 'available': True}
    if specialization:
        query['specialization'] = specialization
    return list(users_collection.find(query))

def create_therapist_profile(therapist_data: Dict) -> None:
    """Create a new therapist profile"""
    users_collection = get_collection('users')
    users_collection.insert_one({
        **therapist_data,
        'is_therapist': True,
        'created_at': datetime.now()
    })

# Therapist Requests
def send_therapist_request(
    client_id: str,
    therapist_id: str,
    client_name: str,
    client_email: str,
    client_phone: str,
    preferred_date: datetime.date,
    preferred_time: datetime.time,
    problem_description: str,
    status: str = 'pending'
) -> None:
    """Send therapist request with appointment details
    
    Args:
        client_id: ID of the client making the request
        therapist_id: ID of the therapist being requested (must be valid ObjectId)
        client_name: Full name of the client
        client_email: Client's contact email
        client_phone: Client's contact phone number
        preferred_date: Preferred appointment date
        preferred_time: Preferred appointment time
        problem_description: Description of client's concerns
        status: Request status (default: 'pending')
    """
    requests_collection = get_collection('therapist_requests')
    
    # Validate required fields
    if not all([client_id, therapist_id, client_name, client_email, client_phone, problem_description]):
        raise ValueError("All required fields must be provided")

    request_data = {
        'client_id': client_id,
        'therapist_id': therapist_id,
        'client_name': client_name,
        'client_email': client_email,
        'client_phone': client_phone,
        'problem_description': problem_description,
        'status': status,
        'created_at': datetime.now()
    }
    
    # Validate and set appointment time
    if preferred_date and preferred_time:
        appointment_datetime = datetime.combine(preferred_date, preferred_time)
        if appointment_datetime < datetime.now():
            raise ValueError("Appointment must be in the future")
        request_data['appointment_datetime'] = appointment_datetime
        
    requests_collection.insert_one(request_data)

def get_pending_requests(therapist_id: str) -> List[Dict]:
    """Get pending therapist requests"""
    requests_collection = get_collection('therapist_requests')
    return list(requests_collection.find({
        'therapist_id': therapist_id,
        'status': 'pending'
    }))

def update_request_status(request_id: str, status: str) -> None:
    """Update status of a therapist request"""
    requests_collection = get_collection('therapist_requests')
    requests_collection.update_one(
        {'_id': request_id},
        {'$set': {'status': status}}
    )

def get_pending_requests_for_user(user_id: str) -> List[Dict]:
    """Get pending requests sent by a user"""
    requests_collection = get_collection('therapist_requests')
    return list(requests_collection.find({
        'client_id': user_id,
        'status': 'pending'
    }))

# Mood Tracking (existing functions)
def get_mood_history(user_id: str, limit: int = 30) -> List[Dict]:
    """Get mood history for a user"""
    mood_collection = get_collection('mood_history')
    return list(mood_collection.find(
        {'user_id': user_id},
        sort=[('date', -1)],
        limit=limit
    ))

# Journal Stats (placeholder - needs implementation)
def get_journal_stats(user_id: str) -> Dict:
    """Get journal statistics for a user"""
    return {
        'entries_count': 0,
        'last_entry': None,
        'mood_average': 0
    }

# Database Initialization
def init_db():
    """Initialize database collections and indexes"""
    client = MongoClient('mongodb://localhost:27017/')
    db = client['mindmate']
    
    # Create indexes
    db.messages.create_index([('sender_id', 1), ('recipient_id', 1)])
    db.messages.create_index([('timestamp', -1)])
    db.notifications.create_index([('user_id', 1), ('read', 1)])
    db.therapist_requests.create_index([('therapist_id', 1), ('status', 1)])
    db.session_notes.create_index([('client_id', 1), ('date', -1)])
