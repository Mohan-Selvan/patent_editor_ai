from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import insert, select, update
from sqlalchemy.orm import Session

# from app.internal.ai import AI, get_ai
from app.internal.data import DOCUMENT_1, DOCUMENT_2
from app.internal.db import Base, SessionLocal, engine, get_db

from app.ai_extended import AI, AIExtended, get_ai

from bs4 import BeautifulSoup

import app.models as models
import app.schemas as schemas
import json

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@asynccontextmanager
async def lifespan(_: FastAPI):
    # Create the database tables
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:

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

    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket(websocket: WebSocket, ai: AIExtended = Depends(get_ai)):
    """WebSocket endpoint for streaming AI document review suggestions."""
    await websocket.accept()
    while True:
        try:
            """
            The AI doesn't expect to receive any HTML.
            You can call ai.review_document to receive suggestions from the LLM.
            Remember, the output from the LLM will not be deterministic, so you may want to validate the output before sending it to the client.
            """
            document_html = await websocket.receive_text()
            logging.info("Received data via websocket")

            # Extract text from HTML as the model will not accept HTML
            text = BeautifulSoup(document_html, "html.parser").get_text()

            buffer = ""
            async for chunk in ai.review_document(text):
                if not chunk:
                    continue

                buffer += chunk
                try:
                    parsed = json.loads(buffer)
                    suggestions = schemas.Suggestions(**parsed)
                    await websocket.send_json(suggestions.dict())
                    logging.info("AI suggestions generated")
                    buffer = ""
                except json.JSONDecodeError:
                    continue

        except WebSocketDisconnect:
            break
        except Exception as e:
            logging.error(f"Error occurred: {e}")
            await websocket.send_json({"error": "Suggestion generation failed"})
            continue


#-- DOCUMENT VERSIONING --##

@app.get("/document/{document_id}")
def get_document(
    document_id: int, db: Session = Depends(get_db)
) -> schemas.DocumentVersionOut:
    """Get a document from the database"""

    if document_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid document ID")

    doc = db.scalar(select(models.Document).where(models.Document.id == document_id))
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc_versioned = db.scalar(
        select(models.DocumentVersioned)
        .where(models.DocumentVersioned.document_id == document_id)
        .where(models.DocumentVersioned.version_number == doc.current_version_number)
    )

    if not doc_versioned:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return doc_versioned


@app.post("/documents/{document_id}/versions", response_model=schemas.DocumentVersionOut)
def create_version(document_id: int, version: schemas.DocumentVersionCreate, db: Session = Depends(get_db)):
    """Create a new document version with incremented version number."""

    if document_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid document ID")
    
    if not version.content.strip():
        raise HTTPException(status_code=400, detail="Version content cannot be empty")

    latest_version = db.scalar(
        select(models.DocumentVersioned)
        .where(models.DocumentVersioned.document_id == document_id)
        .order_by(models.DocumentVersioned.version_number.desc())
    )

    new_version_number = (latest_version.version_number if latest_version else 0) + 1

    db_version = models.DocumentVersioned(
        document_id = document_id,
        content = version.content,
        version_number = new_version_number
    )

    db.add(db_version)
    db.commit()

    # Refreshing because date fields (created_at and updated_at) are set by the DB.
    db.refresh(db_version) 
    logging.info(f"New version created - Document {db_version.document_id} - version {db_version.version_number}")

    return switch_version(
        document_id = db_version.document_id, 
        version_number=db_version.version_number, 
        db= db
    )


@app.get("/documents/{document_id}/versions", response_model=list[schemas.DocumentVersionOut])
def list_versions(document_id: int, db: Session = Depends(get_db)):
    """List all versions of a document in ascending order."""

    if document_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid document ID")

    return db.scalars(
        select(models.DocumentVersioned)
        .where(models.DocumentVersioned.document_id == document_id)
        .order_by(models.DocumentVersioned.version_number)
    ).all()


@app.get("/documents/{document_id}/versions/{version_number}", response_model=schemas.DocumentVersionOut)
def get_version(document_id: int, version_number: int, db: Session = Depends(get_db)):
    """Retrieve a specific version of a document."""

    if document_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid document ID")

    return db.scalar(
        select(models.DocumentVersioned)
        .where(models.DocumentVersioned.document_id == document_id)
        .where(models.DocumentVersioned.version_number == version_number)
    )


@app.patch("/documents/{document_id}/versions/{version_number}", response_model=schemas.DocumentVersionOut)
def update_version(document_id: int, version_number:int, version: schemas.DocumentVersionUpdate, db: Session = Depends(get_db)):
    """Update the content of an existing document version, In other words, this saves the document with the updated content."""

    if document_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid document ID")

    db.execute(
        update(models.DocumentVersioned)
        .where(models.DocumentVersioned.document_id == document_id)
        .where(models.DocumentVersioned.version_number == version_number)
        .values(content=version.content)
    )

    db.commit()

    response = db.scalar(
        select(models.DocumentVersioned)
        .where(models.DocumentVersioned.document_id == document_id)
        .where(models.DocumentVersioned.version_number == version_number)
    )

    logging.info(f"Document updated - Document {response.document_id} - version {response.version_number}")
    return response


@app.patch("/documents/{document_id}/switch/{version_number}", response_model=schemas.DocumentVersionOut)
def switch_version(document_id: int, version_number: int, db: Session = Depends(get_db)):
    """Switch the active document version to a specified version."""

    if document_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid document ID")

    target_version = db.scalar(
        select(models.DocumentVersioned)
        .where(models.DocumentVersioned.document_id == document_id)
        .where(models.DocumentVersioned.version_number == version_number)
    )
    
    if not target_version:
        raise HTTPException(status_code=404, detail="Version not found")
    

    db.execute(
        update(models.Document)
        .where(models.Document.id == document_id)
        .values(current_version_number=target_version.version_number)
    )
    db.commit()
    db.refresh(target_version)

    logging.info(f"Document version switched to Document {target_version.document_id} - version {target_version.version_number}")

    return target_version


#== DOCUMENT VERSIONING ==##

#-- AI FEATURES --#

@app.post("/ai/rewrite")
async def request_rewrite(request: schemas.RewriteRequest, ai: AIExtended = Depends(get_ai)):
    """Rewrite a claim using AI to improve clarity and expression."""

    if not request.claim.strip():
        raise HTTPException(status_code=400, detail="Claim text cannot be empty")

    try:
        # Extract text from HTML as the model will not accept HTML
        text = BeautifulSoup(request.content_html, "html.parser").get_text()

        response = await ai.rephrase_text(request.claim, text)
        parsed = json.loads(response)
        return parsed
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI returned invalid JSON")
    except:
        raise HTTPException(status_code=500, detail="Unknown error occured!")


@app.post("/ai/analyze")
async def request_analysis(request: schemas.AnalyzeRequest, ai: AIExtended = Depends(get_ai)):
    """Analyze a document with AI to identify potential issues."""

    if not request.content_html.strip():
        raise HTTPException(status_code=400, detail="Document content cannot be empty")

    try:
        # Extract text from HTML as the model will not accept HTML
        text = BeautifulSoup(request.content_html, "html.parser").get_text()

        response = await ai.analyze_document(text)
        parsed = json.loads(response)
        return parsed
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI returned invalid JSON")
    except:
        raise HTTPException(status_code=500, detail="Unknown error occured!")
    
#== AI FEATURES ==#