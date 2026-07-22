from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from global_context import web_links

from documents import (
    add_web_document,
    remove_web_document,
)

router = APIRouter(
    prefix="/web",
    tags=["Web documents"],
)


class URLRequest(BaseModel):
    url: HttpUrl


@router.get("/")
def get_web_documents():

    return {"documents": web_links}


@router.post("/add")
def add_url(data: URLRequest):

    chunks_added = add_web_document(str(data.url))

    return {
        "message": "URL added successfully",
        "url": str(data.url),
        "chunks_added": chunks_added,
    }


@router.delete("/remove")
def remove_url(data: URLRequest):

    chunks_removed = remove_web_document(str(data.url))

    if chunks_removed == 0:
        raise HTTPException(status_code=404, detail="URL not found")

    return {
        "message": "URL removed successfully",
        "url": str(data.url),
        "chunks_removed": chunks_removed,
    }
