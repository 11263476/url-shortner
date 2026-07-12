from fastapi import status


class TestFolderRoutes:
    async def test_create_folder(self, client, auth_headers, test_workspace):
        resp = await client.post("/api/v1/folders", headers=auth_headers, json={
            "name": "Test Folder",
            "workspace_id": test_workspace.id,
        })
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["name"] == "Test Folder"
        assert data["workspace_id"] == test_workspace.id

    async def test_list_folders(self, client, auth_headers, test_workspace):
        await client.post("/api/v1/folders", headers=auth_headers,
                          json={"name": "Folder A", "workspace_id": test_workspace.id})
        resp = await client.get(f"/api/v1/folders?workspace_id={test_workspace.id}", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert len(data) >= 1

    async def test_rename_folder(self, client, auth_headers, test_workspace):
        create = await client.post("/api/v1/folders", headers=auth_headers,
                                   json={"name": "Old Name", "workspace_id": test_workspace.id})
        folder_id = create.json()["id"]
        resp = await client.put(f"/api/v1/folders/{folder_id}", headers=auth_headers,
                                json={"name": "New Name"})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["name"] == "New Name"

    async def test_delete_folder(self, client, auth_headers, test_workspace):
        create = await client.post("/api/v1/folders", headers=auth_headers,
                                   json={"name": "To Delete", "workspace_id": test_workspace.id})
        folder_id = create.json()["id"]
        resp = await client.delete(f"/api/v1/folders/{folder_id}", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK


class TestTagRoutes:
    async def test_create_tag(self, client, auth_headers, test_workspace):
        resp = await client.post("/api/v1/tags", headers=auth_headers, json={
            "name": "test-tag",
            "workspace_id": test_workspace.id,
        })
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["name"] == "test-tag"

    async def test_list_tags(self, client, auth_headers, test_workspace):
        await client.post("/api/v1/tags", headers=auth_headers,
                          json={"name": "tag1", "workspace_id": test_workspace.id})
        resp = await client.get(f"/api/v1/tags?workspace_id={test_workspace.id}", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()) >= 1

    async def test_delete_tag(self, client, auth_headers, test_workspace):
        create = await client.post("/api/v1/tags", headers=auth_headers,
                                   json={"name": "delete-tag", "workspace_id": test_workspace.id})
        tag_id = create.json()["id"]
        resp = await client.delete(f"/api/v1/tags/{tag_id}", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK


class TestFavoriteRoutes:
    async def test_add_favorite(self, client, auth_headers, test_url):
        resp = await client.post("/api/v1/favorites", headers=auth_headers, json={
            "url_id": test_url.id,
        })
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["url_id"] == test_url.id

    async def test_list_favorites(self, client, auth_headers, test_url):
        await client.post("/api/v1/favorites", headers=auth_headers, json={"url_id": test_url.id})
        resp = await client.get("/api/v1/favorites", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()) >= 1

    async def test_check_favorite(self, client, auth_headers, test_url):
        await client.post("/api/v1/favorites", headers=auth_headers, json={"url_id": test_url.id})
        resp = await client.get(f"/api/v1/favorites/check/{test_url.id}", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["favorited"] is True

    async def test_remove_favorite(self, client, auth_headers, test_url):
        await client.post("/api/v1/favorites", headers=auth_headers, json={"url_id": test_url.id})
        resp = await client.delete(f"/api/v1/favorites/{test_url.id}", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        check = await client.get(f"/api/v1/favorites/check/{test_url.id}", headers=auth_headers)
        assert check.json()["favorited"] is False
