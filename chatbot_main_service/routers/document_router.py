print("11")
from pathlib import Path
print("22")

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
)
print("33")

from documents import (
    add_document,
    remove_document,
)
print("44")

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)
print("55")

DOCUMENTS_FOLDER = Path("documents")
DOCUMENTS_FOLDER.mkdir(exist_ok=True)


@router.get("/")
def get_documents():
    documents = []

    for file in DOCUMENTS_FOLDER.iterdir():
        if file.is_file():
            documents.append({
                "filename": file.name,
                "size": file.stat().st_size,
            })

    documents.sort(key=lambda x: x["filename"])

    return {
        "count": len(documents),
        "documents": documents,
    }

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):

    path = DOCUMENTS_FOLDER / file.filename

    with open(path, "wb") as f:
        f.write(await file.read())

    chunks_added = add_document(str(path))

    print(f"[UPLOAD] {file.filename}")
    print(f"Chunks added: {chunks_added}")

    return {
        "message": "Document uploaded successfully.",
        "filename": file.filename,
        "chunks_added": chunks_added,
    }


@router.delete("/{filename}")
def delete_document(
    filename: str,
):

    path = DOCUMENTS_FOLDER / filename

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    path.unlink()

    chunks_removed = remove_document(filename)

    print(f"[DELETE] {filename}")
    print(f"Chunks removed: {chunks_removed}")

    return {
        "message": "Document deleted successfully.",
        "filename": filename,
        "chunks_removed": chunks_removed,
    }
