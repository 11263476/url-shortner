import sys
from fastapi.testclient import TestClient

# Add backend/src to path
sys.path.insert(0, r"c:\Users\ramat\Desktop\project\url-shortner\backend")
from src.main import app

client = TestClient(app)

def test_health():
    res = client.get("/health")
    print(f"Health check status: {res.status_code}, response: {res.json()}")
    assert res.status_code == 200

if __name__ == "__main__":
    test_health()
