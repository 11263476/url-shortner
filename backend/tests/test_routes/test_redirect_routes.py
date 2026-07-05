from fastapi import status


class TestRedirectRoutes:
    async def test_redirect_active_url(self, client, test_url):
        resp = await client.get(f"/{test_url.short_code}", follow_redirects=False)
        assert resp.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert resp.headers["location"] == test_url.original_url

    async def test_redirect_not_found(self, client):
        resp = await client.get("/nonexistent123", follow_redirects=False)
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_redirect_with_follow(self, client, test_url):
        resp = await client.get(f"/{test_url.short_code}", follow_redirects=True)
        assert resp.status_code == status.HTTP_200_OK

    async def test_post_to_nonexistent_short_code(self, client):
        resp = await client.post("/nonexistent", data={"pwd": "test"}, follow_redirects=False)
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_health(self, client):
        resp = await client.get("/health")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["status"] == "ok"
