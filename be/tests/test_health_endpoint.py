from diaas_testing import expect

from diaas.config import CONFIG


def test_echo(client):
    res = client.get("/api/_/echo")
    assert res.status_code == 200


def test_public_health(client):
    res = client.get("/api/_/health")
    assert res.json == {"data": {"ok": True}}
    assert res.status_code == 200


def test_health_with_token(client):
    res = client.get("/api/_/health?token=" + CONFIG.INTERNAL_API_TOKEN)
    assert res.status_code == 200
    assert expect(res.json) >= {
        "data": {"ok": True, "app": {"ok": True}, "database": {"ok": False}, "runtime": {"ok": True}}
    }
