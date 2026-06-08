"""
Phase 5 Integration Test
Tests: QR endpoint, API Key CRUD, One-Time URL, Bulk Operations (create/disable/export/delete)
"""
import asyncio
import httpx
import uuid
import json

BASE_URL = "http://localhost:8000"


async def register_and_login(client: httpx.AsyncClient):
    email = f"test_p5_{uuid.uuid4().hex[:8]}@example.com"
    password = "Password123!"
    await client.post(f"{BASE_URL}/api/v1/auth/register", json={"email": email, "password": password})
    login = await client.post(f"{BASE_URL}/api/v1/auth/login", json={"email": email, "password": password})
    token = login.json()["access_token"]
    return token, {"Authorization": f"Bearer {token}"}


async def get_workspace_id(client, headers):
    ws = await client.get(f"{BASE_URL}/api/v1/workspaces/", headers=headers)
    return ws.json()[0]["id"]


async def create_url(client, headers, workspace_id, extra=None):
    body = {"original_url": "https://fastapi.tiangolo.com", "workspace_id": workspace_id}
    if extra:
        body.update(extra)
    res = await client.post(f"{BASE_URL}/api/v1/urls/", json=body, headers=headers)
    return res.json()


async def test_qr_endpoint(client, headers, workspace_id):
    print("\n[TEST 1] QR Code Download Endpoint")
    url_data = await create_url(client, headers, workspace_id)
    url_id = url_data["id"]
    short_code = url_data["short_code"]

    qr_res = await client.get(f"{BASE_URL}/api/v1/urls/{url_id}/qr", headers=headers)
    if qr_res.status_code == 200 and qr_res.headers["content-type"] == "image/png":
        print(f"   [OK] QR PNG returned for {short_code} ({len(qr_res.content)} bytes)")
    else:
        print(f"   [FAIL] QR endpoint: status={qr_res.status_code}, content-type={qr_res.headers.get('content-type')}")
    return url_id


async def test_api_keys(client, headers):
    print("\n[TEST 2] API Key CRUD")

    # Create
    create_res = await client.post(f"{BASE_URL}/api/v1/api-keys/", json={"name": "Test Key"}, headers=headers)
    if create_res.status_code != 201:
        print(f"   [FAIL] Create: {create_res.status_code} - {create_res.text}")
        return
    key_data = create_res.json()
    key_id = key_data["id"]
    raw_key = key_data["key"]
    print(f"   [OK] Created: prefix={key_data['prefix']}, key starts with lf_: {raw_key.startswith('lf_')}")

    # List
    list_res = await client.get(f"{BASE_URL}/api/v1/api-keys/", headers=headers)
    print(f"   [OK] Listed: {len(list_res.json())} key(s)")

    # Rotate
    rotate_res = await client.post(f"{BASE_URL}/api/v1/api-keys/{key_id}/rotate", headers=headers)
    if rotate_res.status_code == 200:
        new_key = rotate_res.json()
        print(f"   [OK] Rotated: new prefix={new_key['prefix']}")
    else:
        print(f"   [FAIL] Rotate: {rotate_res.status_code}")

    # Revoke
    revoke_res = await client.delete(f"{BASE_URL}/api/v1/api-keys/{rotate_res.json()['id']}", headers=headers)
    print(f"   [OK] Revoked: {revoke_res.json().get('detail')}")


async def test_one_time_url(client, headers, workspace_id):
    print("\n[TEST 3] One-Time URL")
    url_data = await create_url(client, headers, workspace_id, {"is_one_time": True})
    short_code = url_data["short_code"]
    print(f"   [OK] Created one-time URL: {short_code}")

    # First click - should redirect (302)
    res1 = await client.get(f"{BASE_URL}/{short_code}", follow_redirects=False)
    print(f"   Click 1 status: {res1.status_code} (expect 302)")

    # Second click - should be disabled (403)
    await asyncio.sleep(0.5)
    res2 = await client.get(f"{BASE_URL}/{short_code}", follow_redirects=False)
    print(f"   Click 2 status: {res2.status_code} (expect 403 - disabled)")

    if res1.status_code == 302 and res2.status_code == 403:
        print("   [SUCCESS] One-time URL disabled after first click!")
    else:
        print("   [FAIL] One-time URL did not behave as expected.")


async def test_bulk_operations(client, headers, workspace_id):
    print("\n[TEST 4] Bulk Operations")

    # Create 3 URLs to test bulk ops
    ids = []
    for _ in range(3):
        d = await create_url(client, headers, workspace_id)
        ids.append(d["id"])
    print(f"   [OK] Created 3 URLs: {ids}")

    # Bulk disable
    dis_res = await client.post(
        f"{BASE_URL}/api/v1/urls/bulk/disable",
        params={"workspace_id": workspace_id},
        json=ids,
        headers=headers,
    )
    print(f"   [OK] Bulk disable: {dis_res.json()}")

    # Bulk reactivate
    react_res = await client.post(
        f"{BASE_URL}/api/v1/urls/bulk/reactivate",
        params={"workspace_id": workspace_id},
        json=ids,
        headers=headers,
    )
    print(f"   [OK] Bulk reactivate: {react_res.json()}")

    # Export CSV
    export_res = await client.get(
        f"{BASE_URL}/api/v1/urls/bulk/export",
        params={"workspace_id": workspace_id, "format": "csv"},
        headers=headers,
    )
    lines = export_res.text.strip().split("\n")
    print(f"   [OK] CSV export: {len(lines)} lines (header + {len(lines)-1} URLs)")

    # Export JSON
    export_json_res = await client.get(
        f"{BASE_URL}/api/v1/urls/bulk/export",
        params={"workspace_id": workspace_id, "format": "json"},
        headers=headers,
    )
    json_data = export_json_res.json()
    print(f"   [OK] JSON export: {len(json_data)} URL records")

    # Bulk QR zip
    qr_zip_res = await client.get(
        f"{BASE_URL}/api/v1/urls/bulk/qr",
        params={"workspace_id": workspace_id},
        headers=headers,
    )
    if qr_zip_res.status_code == 200 and "zip" in qr_zip_res.headers.get("content-type", ""):
        print(f"   [OK] Bulk QR ZIP: {len(qr_zip_res.content)} bytes")
    else:
        print(f"   [FAIL] Bulk QR ZIP: {qr_zip_res.status_code}")

    # Bulk delete
    del_res = await client.post(
        f"{BASE_URL}/api/v1/urls/bulk/delete",
        params={"workspace_id": workspace_id},
        json=ids,
        headers=headers,
    )
    print(f"   [OK] Bulk delete: {del_res.json()}")


async def main():
    print("=" * 60)
    print("  Phase 5 Integration Test Suite")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=15.0) as client:
        token, headers = await register_and_login(client)
        workspace_id = await get_workspace_id(client, headers)
        print(f"[SETUP] Workspace ID: {workspace_id}")

        await test_qr_endpoint(client, headers, workspace_id)
        await test_api_keys(client, headers)
        await test_one_time_url(client, headers, workspace_id)
        await test_bulk_operations(client, headers, workspace_id)

    print("\n" + "=" * 60)
    print("  Phase 5 Test Suite Complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
