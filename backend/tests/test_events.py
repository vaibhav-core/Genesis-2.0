"""
Tests for public events endpoints.
"""

import pytest


class TestEventsPublic:
    """Test public events endpoints."""
    
    def test_get_all_events(self, client, test_db):
        """GET /api/events returns all events."""
        from app.models import Event
        
        # Create events
        events = [
            Event(name="Freshers Party", description="Welcome event"),
            Event(name="Awards Ceremony", description="Prize distribution"),
        ]
        
        for event in events:
            test_db.add(event)
        test_db.commit()
        
        response = client.get("/api/events")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Freshers Party"
        assert data[1]["name"] == "Awards Ceremony"
    
    def test_get_single_event(self, client, test_db):
        """GET /api/events/{id} returns single event."""
        from app.models import Event
        
        event = Event(name="Freshers Party", winner="Candidate A")
        test_db.add(event)
        test_db.commit()
        test_db.refresh(event)
        
        response = client.get(f"/api/events/{event.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == event.id
        assert data["name"] == "Freshers Party"
        assert data["winner"] == "Candidate A"
    
    def test_get_event_not_found(self, client):
        """GET /api/events/{id} returns 404 for non-existent event."""
        response = client.get("/api/events/999")
        assert response.status_code == 404
