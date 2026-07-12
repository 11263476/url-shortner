from fastapi import status


class TestURLRoutes:
    async def test_create_url(self, client, auth_headers, test_workspace):
        resp = await client.post("/api/v1/urls", headers=auth_headers, json={
            "original_url": "https://example.com",
            "workspace_id": test_workspace.id,
        })
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["original_url"] == "https://example.com/"
        assert "short_code" in data
        assert data["workspace_id"] == test_workspace.id

    async def test_create_url_with_custom_alias(self, client, auth_headers, test_workspace):
        resp = await client.post("/api/v1/urls", headers=auth_headers, json={
            "original_url": "https://example.com",
            "workspace_id": test_workspace.id,
            "custom_alias": "mycustom",
        })
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["short_code"] == "mycustom"

    async def test_create_url_duplicate_alias(self, client, auth_headers, test_workspace, test_url):
        resp = await client.post("/api/v1/urls", headers=auth_headers, json={
            "original_url": "https://example.com",
            "workspace_id": test_workspace.id,
            "custom_alias": test_url.short_code,
        })
        assert resp.status_code == status.HTTP_409_CONFLICT

    async def test_list_urls(self, client, auth_headers, test_url):
        resp = await client.get("/api/v1/urls", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "items" in data
        assert len(data["items"]) >= 1
        assert "total" in data

    async def test_list_urls_with_pagination(self, client, auth_headers):
        resp = await client.get("/api/v1/urls?skip=0&limit=5", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "items" in data
        assert "total" in data

    async def test_get_url(self, client, auth_headers, test_url):
        resp = await client.get(f"/api/v1/urls/{test_url.id}", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["short_code"] == test_url.short_code

    async def test_get_url_not_found(self, client, auth_headers):
        resp = await client.get("/api/v1/urls/999999", headers=auth_headers)
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_url(self, client, auth_headers, test_url):
        resp = await client.put(f"/api/v1/urls/{test_url.id}", headers=auth_headers, json={
            "original_url": "https://updated-example.com",
        })
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["original_url"] == "https://updated-example.com/"

    async def test_delete_url(self, client, auth_headers, test_url):
        resp = await client.delete(f"/api/v1/urls/{test_url.id}", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        assert "deleted" in resp.json()["detail"].lower()

    async def test_get_qr_code(self, client, auth_headers, test_url):
        resp = await client.get(f"/api/v1/urls/{test_url.id}/qr", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        assert "qr_code" in resp.json()
        assert resp.json()["qr_code"] is not None

    async def test_create_url_no_auth(self, unauth_client, test_workspace):
        resp = await unauth_client.post("/api/v1/urls", json={
            "original_url": "https://example.com",
            "workspace_id": test_workspace.id,
        })
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
