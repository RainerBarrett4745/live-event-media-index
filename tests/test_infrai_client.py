import httpx
import pytest

from game_media_index.infrai_client import InfraiClient, InfraiError


@pytest.mark.parametrize("verification_status", [404, 200, 403])
def test_delete_bucket_verifies_absence(verification_status: int) -> None:
    calls = []

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, request.url.raw_path))
        if request.method == "DELETE":
            return httpx.Response(200, json={"ok": True, "data": {}})
        return httpx.Response(
            verification_status,
            json={"ok": verification_status == 200, "data": {"items": []},
                  "error": {"code": "lookup_failed"}},
        )

    client = InfraiClient("test", transport=httpx.MockTransport(respond))
    try:
        if verification_status == 404:
            client.delete_bucket("test bucket")
        else:
            with pytest.raises(RuntimeError if verification_status == 200 else InfraiError):
                client.delete_bucket("test bucket")
    finally:
        client.close()
    assert calls == [
        ("DELETE", b"/v1/storage/bucket/delete/test%20bucket"),
        ("GET", b"/v1/storage/object/list/test%20bucket"),
    ]
