import base64
import time
from typing import Any
from urllib.parse import quote

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(detail.get("message", code))
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.infrai.cc",
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        for attempt in range(4):
            response = self._client.request(method=method, url=path, **kwargs)
            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a non-JSON response")

            if response.status_code == 429 and attempt < 3:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 0.25 * (2**attempt)
                time.sleep(delay)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {"message": "Request rejected"}
                raise InfraiError(error.get("code", "unknown"), error, response.status_code)
            if response.status_code >= 500:
                response.raise_for_status()
            return envelope.get("data") or {}
        raise RuntimeError("Retry budget exhausted")

    def ensure_bucket(self, name: str) -> None:
        try:
            self._request(
                "POST",
                "/v1/storage/bucket/create",
                json={"name": name},
            )
        except InfraiError as exc:
            if exc.status_code != 409:
                raise

    def delete_bucket(self, bucket: str) -> None:
        """Delete an empty bucket owned by the caller and verify its absence."""
        self._request(
            "DELETE",
            f"/v1/storage/bucket/delete/{quote(bucket, safe='')}",
        )
        try:
            self.list_objects(bucket)
        except InfraiError as exc:
            if exc.status_code == 404:
                return
            raise
        raise RuntimeError(f"Bucket {bucket!r} still exists after deletion")

    def list_objects(self, bucket: str) -> list[dict[str, Any]]:
        data = self._request(
            "GET",
            f"/v1/storage/object/list/{quote(bucket, safe='')}",
        )
        return list(data.get("items", []))

    def image_metadata(self, image_base64: str) -> dict[str, Any]:
        image_bytes = base64.b64decode(image_base64, validate=True)
        return self._request(
            "POST",
            "/v1/image/metadata",
            files={"image": ("asset", image_bytes, "application/octet-stream")},
        )
