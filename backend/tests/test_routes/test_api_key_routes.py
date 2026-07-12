from fastapi import status


class TestApiKeyRoutes:
    async def test_create_api_key(self, client, auth_headers):
        resp = await client.post("/api/v1/api-keys", headers=auth_headers, json={
            "name": "Test Key",
        })
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["name"] == "Test Key"
        assert "key" in data
        assert data["key"].startswith("lf_")

    async def test_list_api_keys(self, client, auth_headers):
        await client.post("/api/v1/api-keys", headers=auth_headers, json={"name": "Key 1"})
        await client.post("/api/v1/api-keys", headers=auth_headers, json={"name": "Key 2"})
        resp = await client.get("/api/v1/api-keys", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert len(data) >= 2
        names = [k["name"] for k in data]
        assert "Key 1" in names
        assert "Key 2" in names

    async def test_revoke_api_key(self, client, auth_headers):
        create_resp = await client.post("/api/v1/api-keys", headers=auth_headers, json={"name": "To Revoke"})
        key_id = create_resp.json()["id"]
        resp = await client.delete(f"/api/v1/api-keys/{key_id}", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        assert "revoked" in resp.json()["detail"].lower()

    async def test_rotate_api_key(self, client, auth_headers):
        create_resp = await client.post("/api/v1/api-keys", headers=auth_headers, json={"name": "To Rotate"})
        key_id = create_resp.json()["id"]
        old_key = create_resp.json()["key"]
        resp = await client.post(f"/api/v1/api-keys/{key_id}/rotate", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["key"].startswith("lf_")
        assert data["key"] != old_key

    async def test_get_quota(self, client, auth_headers):
        create_resp = await client.post("/api/v1/api-keys", headers=auth_headers, json={"name": "Quota Test"})
        key_id = create_resp.json()["id"]
        resp = await client.get(f"/api/v1/api-keys/{key_id}/quota", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "remaining_quota" in data
        assert "daily_limit" in data

    async def test_create_api_key_no_auth(self, unauth_client):
        resp = await unauth_client.post("/api/v1/api-keys", json={"name": "Unauth Key"})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
