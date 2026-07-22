from fastapi import APIRouter

from utils import chat
from schemas import ChatRequest, ChatResponse

from global_context import chat_history

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post("", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):

    answer = chat(
        request.message,
        use_documents_anyway=request.use_documents_anyway,
    )

    return ChatResponse(
        answer=answer,
    )


@router.get("/history")
def get_chat_history():

    return {
        "count": len(chat_history),
        "messages": chat_history,
    }
