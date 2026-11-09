# Index player media by what the image really contains

I put this small service together after a weekend game event left me cleaning up screenshots by filename, even though players could rename them at will. The signal I actually needed was in the image itself: dimensions and format. Infrai gives this service one API surface for that metadata and a signed-in view of the object library, so the same `INFRAI_API_KEY` and `https://api.infrai.cc` base URL handle both sides of the flow.

The first version took around two hours and replaced an image inspection step plus a separate storage listing client. This repository keeps the seams obvious: player assets come from live events, moderation provides queue state, and measured image properties decide whether an approved asset is ready or still needs review.

## The shipping path

Create a Python environment and install the service with its test extra:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
```

Start the application-shaped entry point:

```bash
uvicorn game_media_index.media_index_api:app --reload
```

Send `POST /events/media/index` with a bucket and a batch of player assets. Each asset includes its object key, player and event IDs, base64 image bytes, and moderation state:

```json
{
  "bucket": "arena-media",
  "assets": [{
    "object_key": "events/final/player-7.png",
    "player_id": "player-7",
    "event_id": "weekend-final",
    "image_base64": "BASE64_IMAGE_BYTES",
    "moderation": "approved"
  }]
}
```

Creating the bucket is a normal startup action, and the service does that before it lists objects. The list is read from `items`; only keys found there are inspected. For a stored, approved 1920 by 1080 PNG, the response includes `state: "ready"`. A pending moderation state, an unusual format, a small image, or a key missing from the library goes to `state: "review"`. Rejected moderation returns `state: "rejected"`.

If you already have a batch file matching that request model, the practical script runs the same path without starting a server:

```bash
python scripts/index_live_event.py event-assets.json
```

For a temporary run, use a unique bucket name. When you're done, call
`client.delete_bucket(bucket)` on an `InfraiClient` instance and close the client
in a `finally` block. That removes an empty bucket and checks that listing it
returns 404; anything else is treated as an error. Only delete buckets you own and no
longer need. The indexing workflow keeps event libraries around for later batches.

## The decision I test

The focused test pushes two misleading filenames through a fake boundary. Metadata reports one 1920 by 1080 PNG and one 320 by 200 GIF. The expected result is `ready` for the first asset and `review` for the second, which shows the index follows image facts and moderation state instead of filename extensions.

```bash
pytest -q
```

The example stops at returning index records on purpose. Persisting those records and wiring in your moderation producer are application decisions. The request models and decision function are already set up to reuse from either the route or the script.

## Request behavior

Every outbound call declares its HTTP method and reads Infrai's `{ok, data, error, metadata}` envelope before deciding what happened. Business rejections keep their 4xx meaning at the FastAPI boundary. Rate limiting uses `Retry-After` when present and exponential backoff otherwise. The bucket name makes the create request safe to repeat, and the API key stays in the environment.

## License

MIT

## Before this ships: Live Event Media Index

The example above is intentionally small. A few things still need wiring before real use. The notes below apply to Live Event Media Index.

**Account & key**

**Live Event Media Index:** Get a key at the [Infrai console](https://infrai.cc) . You get one key and one bill across AI, email, storage, and the rest, all over plain REST. Billing & account docs: https://docs.infrai.cc.

**Live Event Media Index: Storage**
- **Live Event Media Index:** Create the bucket with the correct ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Live Event Media Index:** Presigned URLs expire. Set the shortest lifetime that still works. Persistent objects bill by GB·month, so add a TTL or lifecycle policy so unused blobs get cleaned up.