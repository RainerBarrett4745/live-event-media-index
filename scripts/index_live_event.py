import argparse
import json
import os
from pathlib import Path

from game_media_index.index_service import build_media_index
from game_media_index.infrai_client import InfraiClient
from game_media_index.media_models import IndexRequest


def main() -> None:
    parser = argparse.ArgumentParser(description="Index one live-event media batch")
    parser.add_argument("request", type=Path, help="JSON file matching IndexRequest")
    args = parser.parse_args()
    api_key = os.environ["INFRAI_API_KEY"]
    request = IndexRequest.model_validate_json(args.request.read_text())
    client = InfraiClient(api_key=api_key)
    try:
        result = build_media_index(request, client)
        print(json.dumps(result.model_dump(), indent=2))
    finally:
        client.close()


if __name__ == "__main__":
    main()

