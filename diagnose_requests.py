from mindmate.utils import db

def check_requests():
    """Diagnose why requests aren't appearing in therapist portal"""
    # Get sample therapist ID (first therapist in database)
    therapists = db.get_available_therapists()
    if not therapists:
        print("No therapists found in database")
        return
        
    therapist_id = therapists[0]['_id']
    print(f"Checking requests for therapist: {therapist_id}")
    
    # Check pending requests
    requests = db.get_pending_requests(therapist_id)
    print(f"\nFound {len(requests)} pending requests:")
    for req in requests:
        print(f"- Request ID: {req['_id']}")
        print(f"  Client: {req['client_name']} ({req['client_email']})")
        print(f"  Status: {req['status']}")
        print(f"  Created: {req['created_at']}")
    
    # Verify therapist ID format
    print("\nTherapist ID format check:")
    print(f"Type: {type(therapist_id)}")
    print(f"Sample request therapist_id type: {type(requests[0]['therapist_id']) if requests else 'N/A'}")
    
    # Check all requests in collection
    requests_collection = db.get_collection('therapist_requests')
    total_requests = requests_collection.count_documents({})
    print(f"\nTotal requests in database: {total_requests}")
    print(f"Pending requests: {requests_collection.count_documents({'status': 'pending'})}")
    print(f"Accepted requests: {requests_collection.count_documents({'status': 'accepted'})}")
    print(f"Declined requests: {requests_collection.count_documents({'status': 'declined'})}")
    
if __name__ == '__main__':
    check_requests()
