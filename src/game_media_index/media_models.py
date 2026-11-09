from enum import Enum
import json
from dataclasses import asdict, dataclass
from typing import Any

try:
    from pydantic import BaseModel, Field
except ModuleNotFoundError:
    BaseModel = None  # type: ignore[assignment,misc]


class ModerationState(str, Enum):
    APPROVED = "approved"
    PENDING = "pending"
    REJECTED = "rejected"


if BaseModel is not None:
    class PlayerAsset(BaseModel):
        object_key: str = Field(min_length=1)
        player_id: str = Field(min_length=1)
        event_id: str = Field(min_length=1)
        image_base64: str = Field(min_length=1)
        moderation: ModerationState


    class IndexRequest(BaseModel):
        bucket: str = Field(min_length=3, max_length=63)
        assets: list[PlayerAsset] = Field(min_length=1, max_length=50)


    class IndexedAsset(BaseModel):
        object_key: str
        player_id: str
        event_id: str
        width: int
        height: int
        format: str
        state: str
        reason: str


    class IndexResponse(BaseModel):
        bucket: str
        indexed: list[IndexedAsset]
else:
    @dataclass
    class PlayerAsset:
        object_key: str
        player_id: str
        event_id: str
        image_base64: str
        moderation: ModerationState

        def __post_init__(self) -> None:
            for name in ("object_key", "player_id", "event_id", "image_base64"):
                if not isinstance(getattr(self, name), str) or not getattr(self, name):
                    raise ValueError(f"{name} must be a non-empty string")
            self.moderation = ModerationState(self.moderation)


    @dataclass
    class IndexRequest:
        bucket: str
        assets: list[PlayerAsset]

        def __post_init__(self) -> None:
            if not isinstance(self.bucket, str) or not 3 <= len(self.bucket) <= 63:
                raise ValueError("bucket must contain between 3 and 63 characters")
            if not isinstance(self.assets, list) or not 1 <= len(self.assets) <= 50:
                raise ValueError("assets must contain between 1 and 50 items")
            self.assets = [
                item if isinstance(item, PlayerAsset) else PlayerAsset(**item)
                for item in self.assets
            ]

        @classmethod
        def model_validate(cls, value: dict[str, Any]) -> "IndexRequest":
            if not isinstance(value, dict):
                raise ValueError("request must be an object")
            return cls(**value)

        @classmethod
        def model_validate_json(cls, value: str) -> "IndexRequest":
            return cls.model_validate(json.loads(value))


    @dataclass
    class IndexedAsset:
        object_key: str
        player_id: str
        event_id: str
        width: int
        height: int
        format: str
        state: str
        reason: str


    @dataclass
    class IndexResponse:
        bucket: str
        indexed: list[IndexedAsset]

        def model_dump(self) -> dict[str, Any]:
            return asdict(self)
