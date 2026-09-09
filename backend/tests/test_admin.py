"""
Tests for admin authentication and authorization.
"""

import pytest


class TestAdminLogin:
    """Test admin login endpoint."""
    
    def test_login_valid_credentials(self, client, admin_user):
        """Login with valid credentials returns token."""
        response = client.post(
            "/api/admin/login",
            json={"username": "testadmin", "password": "testpassword"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    def test_login_invalid_password(self, client, admin_user):
        """Login with invalid password fails."""
        response = client.post(
            "/api/admin/login",
            json={"username": "testadmin", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"]
    
    def test_login_invalid_username(self, client, admin_user):
        """Login with non-existent username fails."""
        response = client.post(
            "/api/admin/login",
            json={"username": "nonexistent", "password": "anypassword"}
        )
        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"]


class TestAdminAuthentication:
    """Test admin endpoint authentication."""
    
    def test_admin_endpoint_no_token(self, client, sample_students):
        """Admin endpoint rejects request without token."""
        response = client.get("/api/admin/votes")
        assert response.status_code == 401
    
    def test_admin_endpoint_invalid_token(self, client, sample_students):
        """Admin endpoint rejects request with invalid token."""
        response = client.get(
            "/api/admin/votes",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert response.status_code == 401
    
    def test_admin_endpoint_garbage_token(self, client, sample_students):
        """Admin endpoint rejects request with garbage token."""
        response = client.get(
            "/api/admin/votes",
            headers={"Authorization": "Bearer garbage"}
        )
        assert response.status_code == 401
    
    def test_admin_endpoint_missing_bearer(self, client, sample_students):
        """Admin endpoint rejects request with malformed auth header."""
        response = client.get(
            "/api/admin/votes",
            headers={"Authorization": "InvalidToken"}
        )
        assert response.status_code == 401
    
    def test_admin_endpoint_with_valid_token(self, client, admin_token, sample_students):
        """Admin endpoint accepts valid token."""
        response = client.get(
            "/api/admin/votes",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200


class TestAdminVotes:
    """Test admin vote records endpoint."""
    
    def test_get_votes_empty(self, client, admin_token):
        """Get votes returns empty list when no votes."""
        response = client.get(
            "/api/admin/votes",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_get_votes_with_registered_and_free_data(self, client, admin_token, sample_students, sample_candidates, test_db):
        """Get admin votes includes registered and free-mode votes."""
        from app.models import Vote
        
        # Create votes
        votes = [
            Vote(voter_id=sample_students[0].id, event_id=1, candidate_id=1),
            Vote(voter_id=sample_students[1].id, event_id=1, candidate_id=1),
            Vote(free_voter_identifier="24CS099", event_id=1, candidate_id=2),
        ]
        
        for vote in votes:
            test_db.add(vote)
        test_db.commit()
        
        # Get votes
        response = client.get(
            "/api/admin/votes",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        
        # Check structure
        for record in data:
            assert "voter_name" in record
            assert "voter_roll_number" in record
            assert "candidate_name" in record
            assert "event_id" in record
            assert "created_at" in record
        
        # Check content
        assert {record["voter_roll_number"] for record in data if record["voter_roll_number"]} == {"24ME001", "24ME002"}
        assert {record["candidate_name"] for record in data} == {"Candidate A", "Candidate B"}
        free_vote = next(record for record in data if record["free_voter_identifier"] == "24CS099")
        assert free_vote["voter_name"] == "Free vote"
        assert free_vote["voter_roll_number"] is None

    def test_wipe_votes_deletes_votes_and_clears_winners(self, client, admin_token, sample_students, sample_candidates, test_db):
        from app.models import Event, Vote

        competition = test_db.query(Event).filter(Event.id == 1).first()
        competition.winner = "Old winner"
        test_db.add(Vote(event_id=1, candidate_id=1, voter_id=sample_students[0].id))
        test_db.add(Vote(event_id=1, candidate_id=2, free_voter_identifier="FREE1"))
        test_db.commit()

        response = client.delete("/api/admin/votes", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        assert response.json()["deleted"] == 2
        assert test_db.query(Vote).count() == 0
        test_db.refresh(competition)
        assert competition.winner is None
        assert competition.winner_participant_id is None


class TestAdminCandidates:
    """Test admin candidate management."""
    
    def test_create_candidate(self, client, admin_token, test_db):
        """Create a new candidate."""
        from app.models import Event
        competition = Event(name="Best Dancer", is_competitive=True, voting_enabled=True)
        test_db.add(competition)
        test_db.commit()
        test_db.refresh(competition)
        response = client.post(
            "/api/admin/candidates",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "New Candidate",
                "event_id": competition.id,
                "gender": "other",
                "photo": "https://example.com/photo.jpg"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Candidate"
        assert data["event_id"] == competition.id
        assert data["gender"] == "other"
        assert data["active"] is True

    def test_update_event(self, client, admin_token, test_db):
        from app.models import Event
        event = Event(name="Schedule Entry")
        test_db.add(event)
        test_db.commit()
        test_db.refresh(event)
        response = client.patch(
            f"/api/admin/events/{event.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"location": "Main Hall", "voting_enabled": True, "competition_format": "team"},
        )
        assert response.status_code == 200
        assert response.json()["location"] == "Main Hall"
        assert response.json()["competition_format"] == "team"
        assert response.json()["voting_enabled"] is True
    
    def test_update_candidate(self, client, admin_token, sample_candidates):
        """Update a candidate."""
        response = client.patch(
            "/api/admin/candidates/1",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"active": False}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["active"] is False
    
    def test_update_candidate_not_found(self, client, admin_token):
        """Update non-existent candidate returns 404."""
        response = client.patch(
            "/api/admin/candidates/999",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Updated Name"}
        )
        assert response.status_code == 404


class TestAdminEvents:
    """Test admin event management."""
    
    def test_create_event(self, client, admin_token):
        """Create a new event."""
        response = client.post(
            "/api/admin/events",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Freshers Party",
                "description": "Welcome event",
                "start_time": "2024-01-20T18:00:00",
                "end_time": "2024-01-20T22:00:00"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Freshers Party"
        assert data["winner"] is None

    def test_delete_event(self, client, admin_token, test_db):
        from app.models import Event

        event = Event(name="Removable Event")
        test_db.add(event)
        test_db.commit()
        test_db.refresh(event)

        response = client.delete(
            f"/api/admin/events/{event.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 204
        assert test_db.query(Event).filter_by(id=event.id).first() is None

    def test_pass_distribution_override(self, client, admin_token, test_db):
        from app.models import Event
        from datetime import datetime, timedelta
        event = Event(name="Future Event", start_time=datetime.utcnow() + timedelta(days=1))
        test_db.add(event)
        test_db.commit()
        test_db.refresh(event)
        response = client.patch(
            f"/api/admin/events/{event.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"pass_distribution_enabled_override": True},
        )
        assert response.status_code == 200
        assert response.json()["pass_distribution_enabled_override"] is True
    
    def test_set_event_winner(self, client, admin_token, test_db):
        """Set winner for an event."""
        from app.models import Event
        
        # Create event
        event = Event(name="Freshers Party", is_competitive=True)
        test_db.add(event)
        test_db.commit()
        test_db.refresh(event)
        
        # Set winner
        response = client.post(
            f"/api/admin/events/{event.id}/winner",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"winner": "Candidate A"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["winner"] == "Candidate A"
    
    def test_set_event_winner_not_found(self, client, admin_token):
        """Set winner for non-existent event returns 404."""
        response = client.post(
            "/api/admin/events/999/winner",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"winner": "Someone"}
        )
        assert response.status_code == 404
