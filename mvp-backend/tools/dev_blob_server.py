#!/usr/bin/env python3
"""Local S3 emulator for the blob/photo surfaces (moto, in-memory).

Starts a moto S3 server on 127.0.0.1:9333 and creates the dev bucket, so the
local backend can run the full presign → PUT → attach → presigned-read chain
without any real bucket. State lives in memory — restart = empty bucket,
which is fine for UI iteration (avatars re-upload in seconds).

Usage:
    source .venv/bin/activate           # moto comes from requirements-dev.txt
    python tools/dev_blob_server.py     # blocks; Ctrl-C to stop

Then make sure .env carries the matching BLOB_* block (see env.example's
"local moto" values) and restart uvicorn so it re-reads .env.

Simulator-only by nature: presigned URLs point at 127.0.0.1, which a physical
phone can never reach. For device testing use a real (dev) bucket instead.
NEVER point BLOB_* at the prod bucket locally — tests/test_blobs.py guards it.
"""
from __future__ import annotations

import signal
import sys

HOST = "127.0.0.1"
PORT = 9333
BUCKET = "photos-blob-local"


def main() -> None:
    try:
        from moto.server import ThreadedMotoServer
    except ImportError:
        sys.exit("moto is not installed — run: pip install -r requirements-dev.txt")
    import boto3

    server = ThreadedMotoServer(ip_address=HOST, port=PORT)
    server.start()

    client = boto3.client(
        "s3",
        endpoint_url=f"http://{HOST}:{PORT}",
        region_name="us-east-1",
        aws_access_key_id="local-dev",
        aws_secret_access_key="local-dev",
    )
    client.create_bucket(Bucket=BUCKET)

    print(f"[dev-blob] moto S3 up on http://{HOST}:{PORT}, bucket '{BUCKET}' created")
    print("[dev-blob] .env block (uncomment the 'local moto' lines in env.example):")
    print(f"    BLOB_ENDPOINT=http://{HOST}:{PORT}")
    print("    BLOB_REGION=us-east-1")
    print(f"    BLOB_BUCKET={BUCKET}")
    print("    BLOB_ACCESS_KEY_ID=local-dev")
    print("    BLOB_SECRET_ACCESS_KEY=local-dev")
    print("[dev-blob] Ctrl-C to stop (in-memory — bucket empties on exit)")

    signal.sigwait({signal.SIGINT, signal.SIGTERM})
    server.stop()
    print("\n[dev-blob] stopped")


if __name__ == "__main__":
    main()
