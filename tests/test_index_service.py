from typing import Any

from game_media_index.index_service import build_media_index
from game_media_index.media_models import IndexRequest


class FakeBackend:
    def __init__(self) -> None:
        self.created_bucket = ""

    def ensure_bucket(self, name: str) -> None:
        self.created_bucket = name

    def list_objects(self, bucket: str) -> list[dict[str, Any]]:
        return [{"key": "events/final/player-7.png"}, {"key": "events/final/player-8.gif"}]

    def image_metadata(self, image_base64: str) -> dict[str, Any]:
        if image_base64 == "aGlnaC1yZXM=":
            return {"width": 1920, "height": 1080, "format": "PNG"}
        return {"width": 320, "height": 200, "format": "GIF"}


def test_index_uses_metadata_and_moderation_for_queue_decisions() -> None:
    request = IndexRequest.model_validate(
        {
            "bucket": "arena-media",
            "assets": [
                {
                    "object_key": "events/final/player-7.png",
                    "player_id": "player-7",
                    "event_id": "weekend-final",
                    "image_base64": "aGlnaC1yZXM=",
                    "moderation": "approved",
                },
                {
                    "object_key": "events/final/player-8.gif",
                    "player_id": "player-8",
                    "event_id": "weekend-final",
                    "image_base64": "bG93LXJlcw==",
                    "moderation": "approved",
                },
            ],
        }
    )
    backend = FakeBackend()

    result = build_media_index(request, backend)

    assert backend.created_bucket == "arena-media"
    assert [(item.state, item.reason) for item in result.indexed] == [
        ("ready", "approved with playable dimensions and format"),
        ("review", "format needs a curator check"),
    ]

