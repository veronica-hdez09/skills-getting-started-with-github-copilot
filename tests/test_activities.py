import pytest


class TestGetActivities:
    """Test suite for GET /activities endpoint"""

    def test_get_all_activities(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response is a dictionary
        assert isinstance(data, dict)
        
        # Verify all expected activities are present
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Art Studio",
            "Drama Club",
            "Debate Team",
            "Science Club"
        ]
        for activity_name in expected_activities:
            assert activity_name in data
        
    def test_activity_structure(self, client):
        """Test that activity objects have correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        # Check first activity for required fields
        chess_club = data["Chess Club"]
        
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)
        
    def test_participants_list(self, client):
        """Test that participants list is populated correctly"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert len(chess_club["participants"]) == 2
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignupForActivity:
    """Test suite for POST /activities/{activity_name}/signup endpoint"""
    
    def test_successful_signup(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]
    
    def test_signup_duplicate_student(self, client):
        """Test that duplicate signups are prevented"""
        # First signup succeeds
        response1 = client.post(
            "/activities/Chess%20Club/signup?email=duplicate@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = client.post(
            "/activities/Chess%20Club/signup?email=duplicate@mergington.edu"
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_nonexistent_activity(self, client):
        """Test signup for activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_multiple_different_students(self, client):
        """Test multiple different students can sign up for same activity"""
        student1 = "student1@mergington.edu"
        student2 = "student2@mergington.edu"
        
        response1 = client.post(
            f"/activities/Art%20Studio/signup?email={student1}"
        )
        assert response1.status_code == 200
        
        response2 = client.post(
            f"/activities/Art%20Studio/signup?email={student2}"
        )
        assert response2.status_code == 200
        
        # Verify both students are in participants
        activities_response = client.get("/activities")
        activities = activities_response.json()
        art_studio_participants = activities["Art Studio"]["participants"]
        assert student1 in art_studio_participants
        assert student2 in art_studio_participants


class TestUnregisterFromActivity:
    """Test suite for DELETE /activities/{activity_name}/signup endpoint"""
    
    def test_successful_unregister(self, client):
        """Test successful unregistration from an activity"""
        # First, sign up a student
        client.post(
            "/activities/Chess%20Club/signup?email=todelete@mergington.edu"
        )
        
        # Then unregister them
        response = client.delete(
            "/activities/Chess%20Club/signup?email=todelete@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "todelete@mergington.edu" not in activities["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_participant(self, client):
        """Test unregistration for participant not in activity"""
        response = client.delete(
            "/activities/Chess%20Club/signup?email=notexist@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Participant not found" in data["detail"]
    
    def test_unregister_nonexistent_activity(self, client):
        """Test unregistration from activity that doesn't exist"""
        response = client.delete(
            "/activities/Nonexistent%20Activity/signup?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_existing_participant(self, client):
        """Test unregistration of a participant that was originally registered"""
        # Michael is already signed up for Chess Club
        response = client.delete(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        
        assert response.status_code == 200
        
        # Verify removal
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in activities["Chess Club"]["participants"]


class TestIntegrationScenarios:
    """Integration tests for complex scenarios"""
    
    def test_signup_then_unregister_workflow(self, client):
        """Test complete workflow of signing up and unregistering"""
        email = "workflow@mergington.edu"
        activity = "Programming%20Class"
        
        # Signup
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        get_response = client.get("/activities")
        activities = get_response.json()
        assert email in activities["Programming Class"]["participants"]
        
        # Unregister
        delete_response = client.delete(
            f"/activities/{activity}/signup?email={email}"
        )
        assert delete_response.status_code == 200
        
        # Verify unregister
        get_response2 = client.get("/activities")
        activities2 = get_response2.json()
        assert email not in activities2["Programming Class"]["participants"]
    
    def test_participant_count_updates(self, client):
        """Test that participant count updates correctly"""
        email = "counter@mergington.edu"
        activity = "Art%20Studio"
        
        # Get initial count
        response1 = client.get("/activities")
        initial_count = len(response1.json()["Art Studio"]["participants"])
        
        # Sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Check increased count
        response2 = client.get("/activities")
        after_signup_count = len(response2.json()["Art Studio"]["participants"])
        assert after_signup_count == initial_count + 1
        
        # Unregister
        client.delete(f"/activities/{activity}/signup?email={email}")
        
        # Check decreased count
        response3 = client.get("/activities")
        after_unregister_count = len(response3.json()["Art Studio"]["participants"])
        assert after_unregister_count == initial_count
