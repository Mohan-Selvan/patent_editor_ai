from typing import List, Literal
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class DocumentBase(BaseModel):
    id: int

class DocumentRead(DocumentBase):
    model_config = ConfigDict(from_attributes=True)
    content: str
    version_number: int

class DocumentVersionCreate(BaseModel):
    content: str

class DocumentVersionUpdate(BaseModel):
    content: str

class DocumentVersionOut(BaseModel):
    document_id: int
    version_number: int
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

######################################

class Issue(BaseModel):
    type: str
    severity: Literal["high", "medium", "low"]
    paragraph: int
    description: str
    suggestion: str

class Suggestions(BaseModel):
    issues: List[Issue]

class RewriteRequest(BaseModel):
    claim: str
    content_html: str

class AnalyzeRequest(BaseModel):
    content_html: str