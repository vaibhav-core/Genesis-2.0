"""Tests for admin event participant and team management."""

from app.models import Event, Participant, TeamMember


def event(test_db, name="Competition"):
    competition = Event(name=name)
    test_db.add(competition)
    test_db.commit()
    test_db.refresh(competition)
    return competition


def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


def test_create_individual_participant(client, admin_token, test_db):
    competition = event(test_db)
    response = client.post(
        f"/api/admin/events/{competition.id}/participants",
        headers=auth_headers(admin_token),
        json={
            "participant_type": "individual",
            "name": "Rahul Kumar",
            "roll_number": " 24me001 ",
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "event_id": competition.id,
        "participant_type": "individual",
        "name": "Rahul Kumar",
        "roll_number": "24ME001",
        "members": [],
    }


def test_create_team_participant(client, admin_token, test_db):
    competition = event(test_db)
    response = client.post(
        f"/api/admin/events/{competition.id}/participants",
        headers=auth_headers(admin_token),
        json={
            "participant_type": "team",
            "name": "Team Falcon",
            "members": [
                {"name": "Rahul Kumar", "roll_number": " 24me001 "},
                {"name": "Priya Singh", "roll_number": "24me002"},
            ],
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["participant_type"] == "team"
    assert data["roll_number"] is None
    assert [(member["name"], member["roll_number"]) for member in data["members"]] == [
        ("Rahul Kumar", "24ME001"),
        ("Priya Singh", "24ME002"),
    ]


def test_participant_validation(client, admin_token, test_db):
    competition = event(test_db)
    url = f"/api/admin/events/{competition.id}/participants"
    headers = auth_headers(admin_token)

    assert client.post(
        url,
        headers=headers,
        json={"participant_type": "team", "name": "Empty Team", "members": []},
    ).status_code == 422
    assert client.post(
        url,
        headers=headers,
        json={
            "participant_type": "individual",
            "name": "Rahul Kumar",
            "members": [{"name": "Unexpected Member"}],
        },
    ).status_code == 422


def test_participant_event_not_found(client, admin_token):
    response = client.post(
        "/api/admin/events/999/participants",
        headers=auth_headers(admin_token),
        json={"participant_type": "individual", "name": "Rahul Kumar"},
    )
    assert response.status_code == 404


def test_participant_respects_competition_format(client, admin_token, test_db):
    competition = event(test_db)
    competition.competition_format = "team"
    test_db.commit()
    url = f"/api/admin/events/{competition.id}/participants"
    response = client.post(
        url,
        headers=auth_headers(admin_token),
        json={"participant_type": "individual", "name": "Solo"},
    )
    assert response.status_code == 400

    competition.competition_format = "individual"
    test_db.commit()
    response = client.post(
        url,
        headers=auth_headers(admin_token),
        json={"participant_type": "team", "name": "Team", "members": [{"name": "Member"}]},
    )
    assert response.status_code == 400


def test_list_participants_mixed(client, admin_token, test_db):
    competition = event(test_db)
    url = f"/api/admin/events/{competition.id}/participants"
    headers = auth_headers(admin_token)
    client.post(url, headers=headers, json={"participant_type": "individual", "name": "Solo"})
    client.post(
        url,
        headers=headers,
        json={"participant_type": "team", "name": "Team A", "members": [{"name": "Member"}]},
    )

    response = client.get(url, headers=headers)
    assert response.status_code == 200
    assert [participant["participant_type"] for participant in response.json()] == [
        "individual",
        "team",
    ]
    assert response.json()[0]["members"] == []
    assert len(response.json()[1]["members"]) == 1


def test_delete_participant_cascades_team_members(client, admin_token, test_db):
    competition = event(test_db)
    create_response = client.post(
        f"/api/admin/events/{competition.id}/participants",
        headers=auth_headers(admin_token),
        json={"participant_type": "team", "name": "Team A", "members": [{"name": "Member"}]},
    )
    participant_id = create_response.json()["id"]
    assert test_db.query(TeamMember).count() == 1

    response = client.delete(
        f"/api/admin/events/{competition.id}/participants/{participant_id}",
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 204
    assert test_db.query(Participant).filter_by(id=participant_id).first() is None
    assert test_db.query(TeamMember).count() == 0


def test_delete_participant_from_wrong_event_is_not_found(client, admin_token, test_db):
    first = event(test_db, "First")
    second = event(test_db, "Second")
    create_response = client.post(
        f"/api/admin/events/{first.id}/participants",
        headers=auth_headers(admin_token),
        json={"participant_type": "individual", "name": "Solo"},
    )

    response = client.delete(
        f"/api/admin/events/{second.id}/participants/{create_response.json()['id']}",
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 404


def test_set_winner_by_participant(client, admin_token, test_db):
    competition = event(test_db)
    participant_response = client.post(
        f"/api/admin/events/{competition.id}/participants",
        headers=auth_headers(admin_token),
        json={"participant_type": "individual", "name": "Rahul Kumar"},
    )
    participant_id = participant_response.json()["id"]

    response = client.post(
        f"/api/admin/events/{competition.id}/winner",
        headers=auth_headers(admin_token),
        json={"winner_participant_id": participant_id},
    )
    assert response.status_code == 200
    assert response.json()["winner"] == "Rahul Kumar"
    assert response.json()["winner_participant_id"] == participant_id

    test_db.refresh(competition)
    assert competition.winner == "Rahul Kumar"
    assert competition.winner_participant_id == participant_id


def test_winner_participant_must_belong_to_event(client, admin_token, test_db):
    first = event(test_db, "First")
    second = event(test_db, "Second")
    participant_response = client.post(
        f"/api/admin/events/{first.id}/participants",
        headers=auth_headers(admin_token),
        json={"participant_type": "individual", "name": "Solo"},
    )

    response = client.post(
        f"/api/admin/events/{second.id}/winner",
        headers=auth_headers(admin_token),
        json={"winner_participant_id": participant_response.json()["id"]},
    )
    assert response.status_code == 404


def test_text_winner_flow_remains_supported(client, admin_token, test_db):
    competition = event(test_db)
    response = client.post(
        f"/api/admin/events/{competition.id}/winner",
        headers=auth_headers(admin_token),
        json={"winner": "Manual Winner"},
    )
    assert response.status_code == 200
    assert response.json()["winner"] == "Manual Winner"
    assert response.json()["winner_participant_id"] is None


def test_participant_endpoints_require_admin_auth(client, test_db):
    competition = event(test_db)
    url = f"/api/admin/events/{competition.id}/participants"
    assert client.get(url).status_code == 401
    assert client.post(url, json={"participant_type": "individual", "name": "Solo"}).status_code == 401
    assert client.delete(f"{url}/1").status_code == 401
    assert client.post(
        f"/api/admin/events/{competition.id}/winner",
        json={"winner": "Manual Winner"},
    ).status_code == 401