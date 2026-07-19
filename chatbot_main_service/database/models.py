from sqlalchemy import (
    String,
    Text,
    ForeignKey,
    DateTime,
    Boolean,
    func
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from pgvector.sqlalchemy import Vector

from .base import Base



# =========================
# Users
# =========================

class User(Base):

    __tablename__ = "users"


    id: Mapped[int] = mapped_column(
        primary_key=True
    )


    first_name: Mapped[str] = mapped_column(
        String(100)
    )


    last_name: Mapped[str] = mapped_column(
        String(100)
    )


    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True
    )


    password_hash: Mapped[str] = mapped_column(
        String(255)
    )


    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now()
    )


    chat = relationship(
        "Chat",
        back_populates="user",
        uselist=False
    )


    memories = relationship(
        "Memory",
        back_populates="user"
    )



# =========================
# Chats
# =========================

class Chat(Base):

    __tablename__ = "chats"


    id: Mapped[int] = mapped_column(
        primary_key=True
    )


    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True
    )


    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now()
    )


    updated_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )


    user = relationship(
        "User",
        back_populates="chat"
    )


    messages = relationship(
        "Message",
        back_populates="chat"
    )


    documents = relationship(
        "Document",
        back_populates="chat"
    )


    links = relationship(
        "WebSource",
        back_populates="chat"
    )



# =========================
# Messages
# =========================

class Message(Base):

    __tablename__ = "messages"


    id: Mapped[int] = mapped_column(
        primary_key=True
    )


    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chats.id")
    )


    role: Mapped[str] = mapped_column(
        String(20)
    )


    content: Mapped[str] = mapped_column(
        Text
    )


    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now()
    )


    chat = relationship(
        "Chat",
        back_populates="messages"
    )



# =========================
# Documents
# =========================

class Document(Base):

    __tablename__ = "documents"


    id: Mapped[int] = mapped_column(
        primary_key=True
    )


    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chats.id")
    )


    filename: Mapped[str] = mapped_column(
        String(255)
    )


    path: Mapped[str] = mapped_column(
        String(500)
    )


    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now()
    )


    chat = relationship(
        "Chat",
        back_populates="documents"
    )


    chunks = relationship(
        "DocumentChunk",
        back_populates="document"
    )



# =========================
# Document chunks + vectors
# =========================

class DocumentChunk(Base):

    __tablename__ = "document_chunks"


    id: Mapped[int] = mapped_column(
        primary_key=True
    )


    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id")
    )


    content: Mapped[str] = mapped_column(
        Text
    )


    embedding = mapped_column(
        Vector(1024)
    )


    document = relationship(
        "Document",
        back_populates="chunks"
    )



# =========================
# Web links
# =========================

class WebSource(Base):

    __tablename__ = "web_sources"


    id: Mapped[int] = mapped_column(
        primary_key=True
    )


    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chats.id")
    )


    url: Mapped[str] = mapped_column(
        String(1000)
    )


    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )


    chat = relationship(
        "Chat",
        back_populates="links"
    )


    chunks = relationship(
        "WebChunk",
        back_populates="source"
    )



class WebChunk(Base):

    __tablename__ = "web_chunks"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    source_id: Mapped[int] = mapped_column(
        ForeignKey("web_sources.id")
    )

    content: Mapped[str] = mapped_column(
        Text
    )

    embedding = mapped_column(
        Vector(1024)
    )

    source = relationship(
        "WebSource",
        back_populates="chunks"
    )

# =========================
# User memory
# =========================

class Memory(Base):

    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    fact: Mapped[str] = mapped_column(
        Text
    )

    embedding = mapped_column(
        Vector(1024)
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now()
    )

    user = relationship(
        "User",
        back_populates="memories"
    )