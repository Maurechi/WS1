def test_echo(client):
    res = client.get("/api/_/echo")
    assert res.status_code == 200


def test_health(client):
    res = client.get("/api/_/health")
    assert res.json == {}
    assert res.status_code == 200
