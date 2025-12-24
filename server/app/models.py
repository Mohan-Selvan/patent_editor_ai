from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.internal.db import Base


class Document(Base):
    __tablename__ = "document"
    id = Column(Integer, primary_key=True, index=True)
    # content = Column(String)

    current_version_number = Column(Integer, ForeignKey("document_versioned.version_number"), nullable=True)
    versions = relationship("DocumentVersioned", back_populates="document", foreign_keys = "DocumentVersioned.document_id")


# Include your models here, and they will automatically be created as tables in the database on start-up

class DocumentVersioned(Base):    
    __tablename__="document_versioned"
    id = Column(Integer, primary_key = True, index = True)
    document_id  = Column(Integer, ForeignKey("document.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    content = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    document = relationship("Document", back_populates="versions", foreign_keys=[document_id])    

