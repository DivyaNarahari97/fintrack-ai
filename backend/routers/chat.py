import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from auth import get_or_create_user
from models import User
from schemas import ChatRequest
from services.rag import stream_rag_response

router = APIRouter()


@router.post("")
async def chat(
    request: ChatRequest,
    user: User = Depends(get_or_create_user),
) -> StreamingResponse:
    def generate():
        for chunk in stream_rag_response(user.clerk_id, request.message):
            yield f"data: {json.dumps({'text': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
