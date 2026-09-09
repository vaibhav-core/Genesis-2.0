"""
Tests for pass verification endpoint (/api/pass/verify).
"""

import pytest


class TestPassVerification:
    """Test pass/student lookup endpoint."""
    
    def test_lookup_by_roll_found(self, client, sample_students):
        """Lookup by roll number returns student."""
        response = client.post(
            "/api/pass/verify",
            json={"identifier_type": "roll_number", "value": "24ME001"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["student"]["roll_number"] == "24ME001"
        assert data["student"]["name"] == "Rahul Kumar"
    
    def test_lookup_by_roll_normalized(self, client, sample_students):
        """Lookup by roll number with various normalizations."""
        # All should return the same student
        test_cases = ["24ME001", "24me001", " 24ME001 ", "  24me001  "]
        
        for roll in test_cases:
            response = client.post(
                "/api/pass/verify",
                json={"identifier_type": "roll_number", "value": roll}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
            assert data["student"]["roll_number"] == "24ME001"
    
    def test_lookup_by_roll_not_found(self, client, sample_students):
        """Lookup by non-existent roll number returns student_not_found."""
        response = client.post(
            "/api/pass/verify",
            json={"identifier_type": "roll_number", "value": "99XX999"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["reason"] == "student_not_found"
        assert "student" not in data
    
    def test_lookup_by_name_unique(self, client, sample_students):
        """Lookup by unique name returns student."""
        response = client.post(
            "/api/pass/verify",
            json={"identifier_type": "name", "value": "Priya Singh"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["student"]["roll_number"] == "24ME002"
        assert data["student"]["name"] == "Priya Singh"
    
    def test_lookup_by_name_normalized(self, client, sample_students):
        """Lookup by name with various normalizations."""
        test_cases = ["Priya Singh", "priya singh", " Priya Singh ", "  PRIYA SINGH  "]
        
        for name in test_cases:
            response = client.post(
                "/api/pass/verify",
                json={"identifier_type": "name", "value": name}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
            assert data["student"]["roll_number"] == "24ME002"
    
    def test_lookup_by_name_ambiguous(self, client, sample_students):
        """Lookup by ambiguous name returns multiple_students_found."""
        response = client.post(
            "/api/pass/verify",
            json={"identifier_type": "name", "value": "Rahul Kumar"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["reason"] == "multiple_students_found"
        assert "student" not in data
        assert "Multiple students" in data["message"]
    
    def test_lookup_by_name_not_found(self, client, sample_students):
        """Lookup by non-existent name returns student_not_found."""
        response = client.post(
            "/api/pass/verify",
            json={"identifier_type": "name", "value": "Unknown Person"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["reason"] == "student_not_found"
        assert "student" not in data
