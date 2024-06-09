from starlette.testclient import TestClient


def test_exception_handling_endpoint(test_client: TestClient):
    response = test_client.get("/foo")
    assert response.json() == {"value": "bar"}


def test_http_exception_handling_endpoint(test_client: TestClient):
    response = test_client.get("/not-found")
    assert response.status_code == 404
    assert response.json()["detail"] == "Not Found"
