import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, select
from sqlalchemy.orm import sessionmaker

from app import models
from app.__main__ import app
from app.internal.data import DOCUMENT_1, DOCUMENT_2
from app.internal.db import Base
from app.internal.db import get_db

client = TestClient(app)

SQLALCHEMY_DATABASE_URL = "sqlite:///./temp_test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    # Create schema once for all tests
    Base.metadata.create_all(bind=engine)
    with TestingSessionLocal() as db:
        for id, content in [(1, DOCUMENT_1), (2, DOCUMENT_2)]:

            if not db.scalar(select(models.Document).where(models.Document.id == id)):
                doc = models.Document()
                doc.id = id
                doc.current_version_number = 1
                db.add(doc)
                db.commit()
                db.refresh(doc)

                initial_version = models.DocumentVersioned(
                    document_id=doc.id, content=content, version_number=1
                )
                db.add(initial_version)
                db.commit()
                db.refresh(initial_version)


# Use TestingSessionLocal instead of the app's SessionLocal
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db


# ------------------------
# Document Endpoints
# ------------------------

def test_get_document_valid():
    response = client.get("/document/1")
    assert response.status_code == 200
    data = response.json()
    assert "content" in data

def test_get_document_invalid_id():
    response = client.get("/document/0")
    assert response.status_code == 400

def test_get_document_not_found():
    response = client.get("/document/999")
    assert response.status_code == 404

def test_create_version_success():
    response = client.post("/documents/1/versions", json={"content": "New version text"})
    assert response.status_code == 200
    data = response.json()
    assert data["version_number"] > 1
    assert data["content"] == "New version text"

def test_create_version_empty_content():
    response = client.post("/documents/1/versions", json={"content": ""})
    assert response.status_code == 400

def test_list_versions():
    response = client.get("/documents/1/versions")
    assert response.status_code == 200
    versions = response.json()
    assert isinstance(versions, list)
    assert len(versions) >= 1

def test_get_specific_version():
    response = client.get("/documents/1/versions/1")
    assert response.status_code == 200
    data = response.json()
    assert data["version_number"] == 1

def test_get_specific_version_invalid_id():
    response = client.get("/documents/0/versions/1")
    assert response.status_code == 400

def test_update_version_success():
    response = client.patch(
        "/documents/1/versions/1",
        json={"content": "Updated content"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Updated content"

def test_update_version_invalid_id():
    response = client.patch(
        "/documents/0/versions/1",
        json={"content": "Won't work"}
    )
    assert response.status_code == 400

def test_switch_version_success():
    # Create a new version to switch to
    create_res = client.post("/documents/1/versions", json={"content": "Switch target"})
    new_version = create_res.json()["version_number"]

    res = client.patch(f"/documents/1/switch/{new_version}")
    assert res.status_code == 200
    data = res.json()
    assert data["version_number"] == new_version

def test_switch_version_not_found():
    res = client.patch("/documents/1/switch/9999")
    assert res.status_code == 404

def test_switch_version_invalid_id():
    res = client.patch("/documents/0/switch/1")
    assert res.status_code == 400

# ------------------------
# AI Rewrite / Analyze
# ------------------------

# @pytest.mark.asyncio
# async def test_ai_rewrite_success(monkeypatch):
#     async def fake_rephrase_text(claim, context):
#         return json.dumps({"result": {"replacement": "Better claim", "error": ""}})

#     monkeypatch.setattr("app.ai_extended.AIExtended.rephrase_text", fake_rephrase_text)

#     res = client.post(
#         "/ai/rewrite",
#         json={"claim": "Original claim", "content_html": "<p>context</p>"}
#     )
#     assert res.status_code == 200
#     assert res.json()["result"]["replacement"] == "Better claim"

# def test_ai_rewrite_empty_claim():
#     res = client.post("/ai/rewrite", json={"claim": "", "content_html": "context"})
#     assert res.status_code == 400

# @pytest.mark.asyncio
# async def test_ai_rewrite_invalid_json(monkeypatch):
#     async def fake_rephrase_text(claim, context):
#         return "not-json"

#     monkeypatch.setattr("app.ai_extended.AIExtended.rephrase_text", fake_rephrase_text)
#     res = client.post(
#         "/ai/rewrite",
#         json={"claim": "Something", "content_html": "<p>ctx</p>"}
#     )
#     assert res.status_code == 500

# @pytest.mark.asyncio
# async def test_ai_analyze_success(monkeypatch):
#     async def fake_analyze_document(doc):
#         return json.dumps({"result": {"score": 90, "problems": []}})

#     monkeypatch.setattr("app.ai_extended.AIExtended.analyze_document", fake_analyze_document)

#     res = client.post("/ai/analyze", json={"content_html": "<p>doc</p>"})
#     assert res.status_code == 200
#     assert res.json()["result"]["score"] == 90

# def test_ai_analyze_empty_content():
#     res = client.post("/ai/analyze", json={"content_html": ""})
#     assert res.status_code == 400

# @pytest.mark.asyncio
# async def test_ai_analyze_invalid_json(monkeypatch):
#     async def fake_analyze_document(doc):
#         return "not-json"

#     monkeypatch.setattr("app.ai_extended.AIExtended.analyze_document", fake_analyze_document)
#     res = client.post("/ai/analyze", json={"content_html": "<p>doc</p>"})
#     assert res.status_code == 500

# ------------------------
# WebSocket
# ------------------------

# @pytest.mark.asyncio
# async def test_websocket_stream(monkeypatch):
#     async def fake_review_document(text):
#         # Simulate streaming JSON chunks
#         yield json.dumps({"issues": [{"severity": "high", "message": "Test"}]})

#     monkeypatch.setattr("app.ai_extended.AIExtended.review_document", fake_review_document)

#     with client.websocket_connect("/ws") as websocket:
#         websocket.send_text("<p>Some HTML</p>")
#         data = websocket.receive_json()
#         assert "issues" in data
#         assert data["issues"][0]["severity"] == "high"

# @pytest.mark.asyncio
# async def test_websocket_invalid_json(monkeypatch):
#     async def fake_review_document(text):
#         yield "invalid json"
#         yield json.dumps({"issues": [{"severity": "low", "message": "Fallback"}]})

#     monkeypatch.setattr("app.ai_extended.AIExtended.review_document", fake_review_document)

#     with client.websocket_connect("/ws") as websocket:
#         websocket.send_text("<p>Bad JSON</p>")
#         data = websocket.receive_json()
#         assert "issues" in data
