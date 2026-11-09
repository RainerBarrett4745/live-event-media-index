from typing import Any

from .media_models import IndexRequest, IndexResponse, IndexedAsset, ModerationState


def _catalog_state(
    moderation: ModerationState, width: int, height: int, image_format: str
) -> tuple[str, str]:
    if moderation == ModerationState.REJECTED:
        return "rejected", "moderation rejected the asset"
    if moderation == ModerationState.PENDING:
        return "review", "moderation is still pending"
    if image_format.lower() not in {"jpeg", "jpg", "png", "webp"}:
        return "review", "format needs a curator check"
    if width < 640 or height < 360:
        return "review", "dimensions are below the live-event minimum"
    return "ready", "approved with playable dimensions and format"


def build_media_index(request: IndexRequest, backend: Any) -> IndexResponse:
    backend.ensure_bucket(request.bucket)
    stored_keys = {str(item["key"]) for item in backend.list_objects(request.bucket)}
    indexed: list[IndexedAsset] = []

    for asset in request.assets:
        if asset.object_key not in stored_keys:
            indexed.append(
                IndexedAsset(
                    object_key=asset.object_key,
                    player_id=asset.player_id,
                    event_id=asset.event_id,
                    width=0,
                    height=0,
                    format="unknown",
                    state="review",
                    reason="asset is not present in the event library",
                )
            )
            continue

        metadata = backend.image_metadata(asset.image_base64)
        width = int(metadata["width"])
        height = int(metadata["height"])
        image_format = str(metadata["format"])
        state, reason = _catalog_state(asset.moderation, width, height, image_format)
        indexed.append(
            IndexedAsset(
                object_key=asset.object_key,
                player_id=asset.player_id,
                event_id=asset.event_id,
                width=width,
                height=height,
                format=image_format,
                state=state,
                reason=reason,
            )
        )

    return IndexResponse(bucket=request.bucket, indexed=indexed)
