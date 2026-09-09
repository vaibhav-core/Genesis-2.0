"""Tests for admin competition participants and team management."""

import pytest


def create_event(test_db, name="Competition"):
    from app.models import Event

    event = Event(name=name)
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)
    return event


def participant_url(event_id):
    return f"/api/admin/events/{event_id}/participants"


class TestParticipantManagement:
    def test_create_individual_participant(self, client, admin_token, test_db):
        event = create_event(test_db)
        response = client.post(
            participant_url(event.id),
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "participant_type": "individual",
                "name": " Rahul Kumar ",
                "roll_number": " 24me001 ",
            },
        )

        assert response.status_code == 201
        assert response.json() == {
            "id": 1,
            "event_id": event.id,
            "participant_type": "individual",
            "name": " Rahul Kumar ",
            "roll_number": "24ME001",
            "members": [],
        }

    def test_create_team_with_members(self, client, admin_token, test_db):
        event = create_event(test_db)
        response = client.post(
            participant_url(event.id),
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "participant_type": "team",
                "name": "Team Falcon",
                "members": [
                    {"name": "Rahul Kumar", "roll_number": "24me001"},
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

    @pytest.mark.parametrize(
        "payload",
        [
            {"participant_type": "team", "name": "Empty Team", "members": []},
            {"participant_type": "individual", "name": "Rahul", "members": []},
            {"participant_type": "other", "name": "Invalid"},
        ],
    )
    def test_invalid_participant_shapes_rejected(
        self, client, admin_token, test_db, payload
    ):
        event = create_event(test_db)
        response = client.post(
            participant_url(event.id),
            headers={"Authorization": f"Bearer {admin_token}"},
            json=payload,
        )
        assert response.status_code == 422

    def test_nonexistent_event_rejected(self, client, admin_token):
        response = client.post(
            participant_url(999),
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"participant_type": "individual", "name": "Rahul"},
        )
        assert response.status_code == 404

    def test_list_participants_mixes_individuals_and_teams(
        self, client, admin_token, test_db
    ):
        event = create_event(test_db)
        headers = {"Authorization": f"Bearer {admin_token}"}
        client.post(
            participant_url(event.id),
            headers=headers,
            json={"participant_type": "individual", "name": "Rahul"},
        )
        client.post(
            participant_url(event.id),
            headers=headers,
            json={
                "participant_type": "team",
                "name": "Team Falcon",
                "members": [{"name": "Priya", "roll_number": "24me002"}],
            },
        )

        response = client.get(participant_url(event.id), headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert [participant["participant_type"] for participant in data] == [
            "individual",
            "team",
        ]
        assert data[0]["members"] == []
        assert data[1]["members"][0]["roll_number"] == "24ME002"

    def test_delete_participant_cascades_team_members(
        self, client, admin_token, test_db
    ):
        from app.models import TeamMember

        event = create_event(test_db)
        response = client.post(
            participant_url(event.id),
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "participant_type": "team",
                "name": "Team Falcon",
                "members": [{"name": "Rahul"}, {"name": "Priya"}],
            },
        )
        participant_id = response.json()["id"]
        member_ids = [member["id"] for member in response.json()["members"]]

        response = client.delete(
            f"{participant_url(event.id)}/{participant_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 204
        assert test_db.query(TeamMember).filter(TeamMember.id.in_(member_ids)).all() == []

    def test_delete_participant_from_wrong_event_rejected(
        self, client, admin_token, test_db
    ):
        first_event = create_event(test_db, "First")
        second_event = create_event(test_db, "Second")
        response = client.post(
            participant_url(first_event.id),
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"participant_type": "individual", "name": "Rahul"},
        )
        participant_id = response.json()["id"]

        response = client.delete(
            f"{participant_url(second_event.id)}/{participant_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404


class TestParticipantWinners:
    def test_set_winner_by_participant_updates_both_fields(
        self, client, admin_token, test_db
    ):
        event = create_event(test_db)
        response = client.post(
            participant_url(event.id),
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"participant_type": "individual", "name": "Rahul Kumar"},
        )
        participant_id = response.json()["id"]

        response = client.post(
            f"/api/admin/events/{event.id}/winner",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"winner_participant_id": participant_id},
        )
        assert response.status_code == 200
        assert response.json()["winner"] == "Rahul Kumar"
        assert response.json()["winner_participant_id"] == participant_id

    def test_winner_from_another_event_rejected(
        self, client, admin_token, test_db
    ):
        first_event = create_event(test_db, "First")
        second_event = create_event(test_db, "Second")
        response = client.post(
            participant_url(first_event.id),
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"participant_type": "individual", "name": "Rahul"},
        )

        response = client.post(
            f"/api/admin/events/{second_event.id}/winner",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"winner_participant_id": response.json()["id"]},
        )
        assert response.status_code == 404

    def test_text_winner_flow_remains_supported(self, client, admin_token, test_db):
        event = create_event(test_db)
        response = client.post(
            f"/api/admin/events/{event.id}/winner",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"winner": "Manual Winner"},
        )
        assert response.status_code == 200
        assert response.json()["winner"] == "Manual Winner"
        assert response.json()["winner_participant_id"] is None

    @pytest.mark.parametrize(
        "method, path, payload",
        [
            ("get", "/api/admin/events/1/participants", None),
            ("post", "/api/admin/events/1/participants", {"participant_type": "individual", "name": "Rahul"}),
            ("delete", "/api/admin/events/1/participants/1", None),
            ("post", "/api/admin/events/1/winner", {"winner": "Rahul"}),
        ],
    )
    def test_participant_endpoints_require_admin_token(
        self, client, test_db, method, path, payload
    ):
        event = create_event(test_db)
        path = path.replace("/1/", f"/{event.id}/")
        response = getattr(client, method)(path, json=payload) if payload else getattr(client, method)(path)
        assert response.status_code == 401