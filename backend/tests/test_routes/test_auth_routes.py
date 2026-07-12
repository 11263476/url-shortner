from fastapi import status


class TestAuthRoutes:
    async def test_register(self, client):
        resp = await client.post("/api/v1/auth/register", json={
            "email": "newuser@example.com",
            "password": "StrongPass1!",
        })
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "password" not in data

    async def test_register_duplicate(self, client, test_user):
        resp = await client.post("/api/v1/auth/register", json={
            "email": test_user.email,
            "password": "StrongPass1!",
        })
        assert resp.status_code == status.HTTP_409_CONFLICT

    async def test_login_success(self, client, test_user):
        resp = await client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "testpass123",
        })
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client, test_user):
        resp = await client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "wrongpass",
        })
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_login_nonexistent_user(self, client):
        resp = await client.post("/api/v1/auth/login", json={
            "email": "noone@example.com",
            "password": "testpass123",
        })
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_get_me_authenticated(self, client, auth_headers, test_user):
        resp = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["email"] == test_user.email

    async def test_get_me_unauthenticated(self, unauth_client):
        resp = await unauth_client.get("/api/v1/auth/me")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_forgot_password(self, client):
        resp = await client.post("/api/v1/auth/forgot-password", json={
            "email": "test@example.com",
        })
        assert resp.status_code == status.HTTP_200_OK
        assert "sent" in resp.json()["detail"].lower()

    async def test_refresh_invalid_token(self, client):
        resp = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid-token",
        })
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
