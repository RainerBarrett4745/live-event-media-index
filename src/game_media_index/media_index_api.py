import os

from fastapi import FastAPI, HTTPException

from .index_service import build_media_index
from .infrai_client import InfraiClient, InfraiError
from .media_models import IndexRequest, IndexResponse


app = FastAPI(title="Game Media Index")


@app.post("/events/media/index", response_model=IndexResponse)
def index_event_media(request: IndexRequest) -> IndexResponse:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="INFRAI_API_KEY is required")

    client = InfraiClient(api_key=api_key)
    try:
        return build_media_index(request, client)
    except InfraiError as exc:
        client_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=client_status,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc
    finally:
        client.close()

