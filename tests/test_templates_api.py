"""
Tests for Interview Templates API endpoints.
Covers GET/POST/PUT/DELETE /templates and the question-plan integration.
"""

from fastapi.testclient import TestClient

from orchestrator.main import app

client = TestClient(app)


def make_payload(**overrides):
    payload = {
        "name": "Backend Engineer Screen",
        "interview_type": "technical",
        "description": "Screening round for backend engineers",
        "duration_minutes": 45,
        "question_count": 10,
        "category_distribution": {"technical": 60, "behavioral": 40},
    }
    payload.update(overrides)
    return payload


class TestCreateTemplate:
    def test_create_returns_template(self):
        res = client.post("/templates", json=make_payload())
        assert res.status_code == 201
        body = res.json()
        assert body["name"] == "Backend Engineer Screen"
        assert "template_id" in body

    def test_create_invalid_interview_type_returns_400(self):
        res = client.post("/templates", json=make_payload(interview_type="not_a_type"))
        assert res.status_code == 400

    def test_create_distribution_not_100_returns_400(self):
        res = client.post(
            "/templates",
            json=make_payload(category_distribution={"technical": 50, "behavioral": 40}),
        )
        assert res.status_code == 400

    def test_create_negative_percentage_returns_400(self):
        res = client.post(
            "/templates",
            json=make_payload(category_distribution={"technical": 110, "behavioral": -10}),
        )
        assert res.status_code == 400


class TestGetTemplate:
    def test_get_single_existing_template(self):
        created = client.post("/templates", json=make_payload()).json()
        res = client.get(f"/templates/{created['template_id']}")
        assert res.status_code == 200
        assert res.json()["template_id"] == created["template_id"]

    def test_get_nonexistent_returns_404(self):
        res = client.get("/templates/tmpl_does_not_exist")
        assert res.status_code == 404


class TestListTemplates:
    def test_list_returns_templates(self):
        client.post("/templates", json=make_payload())
        res = client.get("/templates")
        assert res.status_code == 200
        assert res.json()["count"] >= 1


class TestUpdateTemplate:
    def test_update_changes_duration(self):
        created = client.post("/templates", json=make_payload()).json()
        payload = make_payload(duration_minutes=90)
        res = client.put(f"/templates/{created['template_id']}", json=payload)
        assert res.status_code == 200
        assert res.json()["duration_minutes"] == 90

    def test_update_nonexistent_returns_404(self):
        payload = make_payload()
        res = client.put("/templates/tmpl_does_not_exist", json=payload)
        assert res.status_code == 404

    def test_update_invalid_distribution_returns_400(self):
        created = client.post("/templates", json=make_payload()).json()
        payload = make_payload(category_distribution={"technical": 200})
        res = client.put(f"/templates/{created['template_id']}", json=payload)
        assert res.status_code == 400


class TestDeleteTemplate:
    def test_delete_existing_template(self):
        created = client.post("/templates", json=make_payload()).json()
        res = client.delete(f"/templates/{created['template_id']}")
        assert res.status_code == 200
        assert res.json()["deleted"] is True

        res = client.get(f"/templates/{created['template_id']}")
        assert res.status_code == 404

    def test_delete_nonexistent_returns_404(self):
        res = client.delete("/templates/tmpl_does_not_exist")
        assert res.status_code == 404


class TestQuestionPlan:
    def test_question_plan_matches_distribution(self):
        created = client.post(
            "/templates",
            json=make_payload(
                question_count=10,
                category_distribution={"technical": 60, "behavioral": 40},
            ),
        ).json()
        res = client.get(f"/templates/{created['template_id']}/question-plan")
        assert res.status_code == 200
        print("QUESTION PLAN RESPONSE:", res.json())
        plan = res.json()["question_plan"]
        assert plan["category_counts"]["technical"] == 6
        assert plan["category_counts"]["behavioral"] == 4
        assert plan["category_counts"]["situational"] == 0

    def test_question_plan_nonexistent_returns_404(self):
        res = client.get("/templates/tmpl_does_not_exist/question-plan")
        assert res.status_code == 404
