"""Tests for event-scoped registered and free voting."""

from app.models import Event, Candidate, Vote


def vote_payload(mode="registered", event_id=1, candidate_id=1, identifier="24ME001"):
    payload = {"mode": mode, "event_id": event_id, "candidate_id": candidate_id}
    if mode == "registered":
        payload.update({"roll_number": identifier, "name": "Rahul Kumar"})
    else:
        payload["voter_identifier"] = identifier
    return payload


def test_registered_vote_success_and_duplicate(client, sample_students, sample_candidates):
    first = client.post("/api/voting/vote", json=vote_payload())
    second = client.post("/api/voting/vote", json=vote_payload(candidate_id=2))
    assert first.json() == {"success": True}
    assert second.json()["reason"] == "already_voted"


def test_registered_verify_identity(client, sample_students, sample_candidates):
    response = client.post("/api/voting/verify", json={
        **vote_payload(), "name": "Wrong Name",
    })
    assert response.status_code == 200
    assert response.json()["reason"] == "identity_mismatch"


def test_free_vote_duplicate_and_cross_event(client, sample_candidates):
    first = client.post("/api/voting/vote", json=vote_payload("free", 1, 1, "24CS099"))
    duplicate = client.post("/api/voting/vote", json=vote_payload("free", 1, 2, "24CS099"))
    other_event = client.post("/api/voting/vote", json=vote_payload("free", 2, 3, "24CS099"))
    assert first.json()["success"] is True
    assert duplicate.json()["reason"] == "already_voted"
    assert other_event.json()["success"] is True


def test_free_identifier_is_normalized(client, sample_candidates):
    first = client.post("/api/voting/vote", json=vote_payload("free", 1, 1, "24cs099"))
    second = client.post("/api/voting/vote", json=vote_payload("free", 1, 2, "24CS099"))
    assert first.json()["success"] is True
    assert second.json()["reason"] == "already_voted"


def test_voting_disabled_and_status_gates(client, test_db):
    event = Event(name="Disabled", is_competitive=True)
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)
    candidate = Candidate(event_id=event.id, name="Candidate")
    test_db.add(candidate)
    test_db.commit()

    disabled = client.post("/api/voting/vote", json=vote_payload("free", event.id, candidate.id, "FREE1"))
    assert disabled.json()["reason"] == "voting_not_enabled"

    event.voting_enabled = True
    test_db.commit()
    not_started = client.post("/api/voting/vote", json=vote_payload("free", event.id, candidate.id, "FREE2"))
    assert not_started.json()["reason"] == "voting_not_open"
    event.voting_status = "closed"
    test_db.commit()
    closed = client.post("/api/voting/vote", json=vote_payload("free", event.id, candidate.id, "FREE3"))
    assert closed.json()["reason"] == "voting_not_open"


def test_voting_start_stop_transitions_and_gate(client, admin_token, test_db):
    event = Event(name="Managed", is_competitive=True, voting_enabled=True)
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)
    candidate = Candidate(event_id=event.id, name="Candidate")
    test_db.add(candidate)
    test_db.commit()
    headers = {"Authorization": f"Bearer {admin_token}"}

    start = client.post(f"/api/admin/events/{event.id}/voting/start", headers=headers)
    assert start.json()["voting_status"] == "open"
    assert client.post("/api/voting/vote", json=vote_payload("free", event.id, candidate.id, "FREE4")).json()["success"] is True
    stop = client.post(f"/api/admin/events/{event.id}/voting/stop", headers=headers)
    assert stop.json()["voting_status"] == "closed"
    assert client.post("/api/voting/vote", json=vote_payload("free", event.id, candidate.id, "FREE5")).json()["reason"] == "voting_not_open"


def test_candidate_creation_requires_voting_enabled(client, admin_token, test_db):
    event = Event(name="No Vote")
    test_db.add(event)
    test_db.commit()
    response = client.post(
        "/api/admin/candidates",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"event_id": event.id, "name": "Candidate"},
    )
    assert response.status_code == 400


def test_candidate_must_belong_to_event(client, sample_candidates):
    response = client.post("/api/voting/vote", json=vote_payload("free", 2, 1, "FREE6"))
    assert response.json()["reason"] == "invalid_candidate"


def test_noncompetitive_event_rejects_voting(client, test_db):
    event = Event(name="Talk", voting_enabled=True, voting_status="open", is_competitive=False)
    test_db.add(event)
    test_db.commit()
    candidate = Candidate(event_id=event.id, name="Not allowed")
    test_db.add(candidate)
    test_db.commit()
    response = client.post("/api/voting/vote", json=vote_payload("free", event.id, candidate.id, "FREE-TALK"))
    assert response.json()["reason"] == "voting_not_enabled"


def test_results_are_event_scoped(client, sample_students, sample_candidates, test_db):
    votes = [
        Vote(voter_id=sample_students[0].id, event_id=1, candidate_id=1),
        Vote(voter_id=sample_students[1].id, event_id=1, candidate_id=1),
        Vote(voter_id=sample_students[2].id, event_id=1, candidate_id=2),
    ]
    test_db.add_all(votes)
    test_db.commit()
    response = client.get("/api/voting/results?event_id=1")
    assert response.status_code == 200
    assert response.json()["event_id"] == 1
    assert response.json()["results"][0]["votes"] == 2
    assert "voter_id" not in response.json()["results"][0]
