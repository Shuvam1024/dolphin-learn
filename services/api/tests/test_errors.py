from app.main import app
from fastapi.testclient import TestClient
from pydantic import BaseModel

client = TestClient(app)


class _Item(BaseModel):
    name: str


@app.post("/api/v1/_validation_probe")
def _validation_probe(item: _Item) -> dict[str, str]:
    return {"name": item.name}


def test_unknown_route_uses_error_envelope() -> None:
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    error = response.json()["error"]
    assert set(error) == {"code", "message", "details", "request_id"}
    assert error["code"] == "not_found"
    assert response.headers["x-request-id"] == error["request_id"]


def test_validation_error_uses_error_envelope() -> None:
    response = client.post("/api/v1/_validation_probe", json={})
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert isinstance(error["details"], list)
    assert error["request_id"]
