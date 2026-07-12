from fastapi import status


class TestWorkspaceRoutes:
    async def test_create_workspace(self, client, auth_headers):
        resp = await client.post("/api/v1/workspaces", headers=auth_headers, json={
            "name": "New Test Workspace",
        })
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["name"] == "New Test Workspace"
        assert "id" in data

    async def test_list_workspaces(self, client, auth_headers, test_workspace):
        resp = await client.get("/api/v1/workspaces", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert len(data) >= 1
        assert any(w["id"] == test_workspace.id for w in data)

    async def test_get_workspace(self, client, auth_headers, test_workspace):
        resp = await client.get(f"/api/v1/workspaces/{test_workspace.id}", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["name"] == test_workspace.name

    async def test_get_workspace_not_found(self, client, auth_headers):
        resp = await client.get("/api/v1/workspaces/999999", headers=auth_headers)
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_rename_workspace(self, client, auth_headers, test_workspace):
        resp = await client.put(f"/api/v1/workspaces/{test_workspace.id}", headers=auth_headers, json={
            "name": "Renamed Workspace",
        })
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["name"] == "Renamed Workspace"

    async def test_delete_workspace(self, client, auth_headers, test_workspace):
        resp = await client.delete(f"/api/v1/workspaces/{test_workspace.id}", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        assert "deleted" in resp.json()["detail"].lower()

    async def test_invite_member(self, client, auth_headers, test_workspace, test_user):
        resp = await client.post(f"/api/v1/workspaces/{test_workspace.id}/invites",
                                 headers=auth_headers, json={
                                     "email": "invited@example.com",
                                     "role": "editor",
                                 })
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["email"] == "invited@example.com"

    async def test_list_members(self, client, auth_headers, test_workspace, test_member):
        resp = await client.get(f"/api/v1/workspaces/{test_workspace.id}/members", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert len(data) >= 1

    async def test_create_workspace_no_auth(self, unauth_client):
        resp = await unauth_client.post("/api/v1/workspaces", json={"name": "Unauth Workspace"})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_update_member_role(self, client, auth_headers, test_workspace, test_member):
        resp = await client.put(f"/api/v1/workspaces/{test_workspace.id}/members/{test_member.id}/role",
                                headers=auth_headers, json={"role": "viewer"})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["role"] == "viewer"
