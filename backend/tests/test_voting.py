"""
Tests for voting endpoints (/api/voting/*).
"""

import pytest


class TestVotingCandidates:
    """Test candidate listing."""
    
    def test_get_candidates_active_only(self, client, sample_candidates):
        """GET /api/voting/candidates returns only active candidates."""
        response = client.get("/api/voting/candidates")
        assert response.status_code == 200
        
        candidates = response.json()
        assert len(candidates) == 3  # 3 active, 1 inactive
        
        # Verify only active candidates
        for candidate in candidates:
            assert candidate["active"] is True or candidate.get("active") != False
        
        # Check specific candidates
        names = {c["name"] for c in candidates}
        assert "Candidate A" in names
        assert "Candidate B" in names
        assert "Candidate C" in names
        assert "Candidate D" not in names  # Inactive
    
    def test_candidates_no_voter_info(self, client, sample_candidates):
        """Candidate list doesn't expose voter information."""
        response = client.get("/api/voting/candidates")
        assert response.status_code == 200
        
        for candidate in response.json():
            assert "voter" not in candidate
            assert "votes" not in candidate


class TestVotingVerification:
    """Test voting eligibility verification."""
    
    def test_verify_eligible_no_vote(self, client, sample_students, sample_candidates):
        """Verify returns valid for eligible student with no vote."""
        response = client.post(
            "/api/voting/verify",
            json={
                "roll_number": "24ME001",
                "name": "Rahul Kumar",
                "category": "Mister Freshers"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["already_voted"] is False
    
    def test_verify_identity_mismatch(self, client, sample_students, sample_candidates):
        """Verify returns identity_mismatch for wrong name."""
        response = client.post(
            "/api/voting/verify",
            json={
                "roll_number": "24ME001",
                "name": "Wrong Name",
                "category": "Mister Freshers"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["reason"] == "identity_mismatch"
    
    def test_verify_student_not_found(self, client, sample_students, sample_candidates):
        """Verify returns student_not_found for unknown roll."""
        response = client.post(
            "/api/voting/verify",
            json={
                "roll_number": "99XX999",
                "name": "Unknown",
                "category": "Mister Freshers"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["reason"] == "student_not_found"


class TestVoteSubmission:
    """Test voting submission."""
    
    def test_vote_success(self, client, sample_students, sample_candidates):
        """Submit a vote successfully."""
        response = client.post(
            "/api/voting/vote",
            json={
                "roll_number": "24ME001",
                "name": "Rahul Kumar",
                "candidate_id": 1,
                "category": "Mister Freshers"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_vote_identity_mismatch(self, client, sample_students, sample_candidates):
        """Vote fails with identity_mismatch."""
        response = client.post(
            "/api/voting/vote",
            json={
                "roll_number": "24ME001",
                "name": "Wrong Name",
                "candidate_id": 1,
                "category": "Mister Freshers"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["reason"] == "identity_mismatch"
    
    def test_vote_student_not_found(self, client, sample_students, sample_candidates):
        """Vote fails with student_not_found."""
        response = client.post(
            "/api/voting/vote",
            json={
                "roll_number": "99XX999",
                "name": "Unknown",
                "candidate_id": 1,
                "category": "Mister Freshers"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["reason"] == "student_not_found"
    
    def test_vote_duplicate_same_category(self, client, sample_students, sample_candidates):
        """Second vote in same category fails with already_voted."""
        # First vote succeeds
        response1 = client.post(
            "/api/voting/vote",
            json={
                "roll_number": "24ME001",
                "name": "Rahul Kumar",
                "candidate_id": 1,
                "category": "Mister Freshers"
            }
        )
        assert response1.status_code == 200
        assert response1.json()["success"] is True
        
        # Second vote in same category fails
        response2 = client.post(
            "/api/voting/vote",
            json={
                "roll_number": "24ME001",
                "name": "Rahul Kumar",
                "candidate_id": 2,
                "category": "Mister Freshers"
            }
        )
        assert response2.status_code == 200
        data = response2.json()
        assert data["success"] is False
        assert data["reason"] == "already_voted"
    
    def test_vote_different_category_allowed(self, client, sample_students, sample_candidates):
        """Vote in different category succeeds after voting in one category."""
        # Vote in Mister Freshers
        response1 = client.post(
            "/api/voting/vote",
            json={
                "roll_number": "24ME001",
                "name": "Rahul Kumar",
                "candidate_id": 1,
                "category": "Mister Freshers"
            }
        )
        assert response1.status_code == 200
        assert response1.json()["success"] is True
        
        # Vote in Miss Freshers (different category)
        response2 = client.post(
            "/api/voting/vote",
            json={
                "roll_number": "24ME001",
                "name": "Rahul Kumar",
                "candidate_id": 3,
                "category": "Miss Freshers"
            }
        )
        assert response2.status_code == 200
        assert response2.json()["success"] is True
    
    def test_vote_inactive_candidate(self, client, sample_students, sample_candidates):
        """Vote fails for inactive candidate."""
        response = client.post(
            "/api/voting/vote",
            json={
                "roll_number": "24ME001",
                "name": "Rahul Kumar",
                "candidate_id": 4,  # Candidate D is inactive
                "category": "Miss Freshers"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["reason"] == "invalid_candidate"


class TestVotingResults:
    """Test voting results aggregation."""
    
    def test_get_results_empty(self, client, sample_candidates):
        """Results for category with no votes."""
        response = client.get("/api/voting/results?category=Mister%20Freshers")
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "Mister Freshers"
        assert len(data["results"]) == 0
    
    def test_get_results_sorted_by_votes(self, client, sample_students, sample_candidates, test_db):
        """Results are sorted by votes descending."""
        from app.models import Vote
        
        # Create votes: candidate 1 gets 3 votes, candidate 2 gets 1 vote
        votes = [
            Vote(voter_id=sample_students[0].id, candidate_id=1, category="Mister Freshers"),
            Vote(voter_id=sample_students[1].id, candidate_id=1, category="Mister Freshers"),
            Vote(voter_id=sample_students[2].id, candidate_id=1, category="Mister Freshers"),
            Vote(voter_id=sample_students[3].id, candidate_id=2, category="Mister Freshers"),
        ]
        
        for vote in votes:
            test_db.add(vote)
        test_db.commit()
        
        # Get results
        response = client.get("/api/voting/results?category=Mister%20Freshers")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["results"]) == 2
        assert data["results"][0]["candidate_id"] == 1
        assert data["results"][0]["votes"] == 3
        assert data["results"][1]["candidate_id"] == 2
        assert data["results"][1]["votes"] == 1
    
    def test_results_no_voter_info(self, client, sample_students, sample_candidates, test_db):
        """Results don't expose voter information."""
        from app.models import Vote
        
        # Create a vote
        vote = Vote(voter_id=sample_students[0].id, candidate_id=1, category="Mister Freshers")
        test_db.add(vote)
        test_db.commit()
        
        response = client.get("/api/voting/results?category=Mister%20Freshers")
        assert response.status_code == 200
        data = response.json()
        
        for result in data["results"]:
            assert "voter" not in result
            assert "voter_id" not in result
            assert "voter_name" not in result
            # Only these fields should be present
            assert set(result.keys()) == {"candidate_id", "name", "votes"}
