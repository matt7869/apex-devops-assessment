from app.main import app


def test_health_endpoint():
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "alive"}


def test_create_operation_rejects_missing_title():
    client = app.test_client()

    response = client.post("/operations", json={})

    assert response.status_code == 400
    assert response.get_json()["error"] == "title must be a non-empty string"


def test_create_operation_rejects_empty_title():
    client = app.test_client()

    response = client.post("/operations", json={"title": "   "})

    assert response.status_code == 400


def test_create_operation_rejects_non_json_body():
    client = app.test_client()

    response = client.post(
        "/operations",
        data="this is not JSON",
        content_type="text/plain",
    )

    assert response.status_code == 400


def test_create_operation_rejects_title_over_200_characters():
    client = app.test_client()

    response = client.post("/operations", json={"title": "x" * 201})
    assert response.status_code == 400
def test_create_operation_rejects_json_list():
    client = app.test_client()

    response = client.post(
        "/operations",
        json=["not", "an", "object"],
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "A JSON object is required"
    }

    assert response.status_code == 400
