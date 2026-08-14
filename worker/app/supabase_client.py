"""
Supabase client for the worker. Uses the SERVICE ROLE key, never the
anon key -- the worker needs to write rows on behalf of a user without
being subject to RLS insert policies (there are none defined for the
score/candidate tables; see the migration). Keep SUPABASE_SERVICE_ROLE_KEY
out of the Next.js app entirely -- it only ever lives in the worker's
environment.
"""

import os
import sys
from supabase import create_client, Client

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        # TEMPORARY DIAGNOSTIC -- remove once the RLS issue is resolved.
        # Decodes the JWT's payload (not the secret) to show which role
        # this key actually is -- should print role='service_role'.
        import base64
        import json
        try:
            payload_segment = key.split(".")[1]
            padded = payload_segment + "=" * (-len(payload_segment) % 4)
            payload = json.loads(base64.urlsafe_b64decode(padded))
            role = payload.get("role", "<no role claim>")
        except Exception as e:
            role = f"<decode failed: {e}>"
        print(
            f"DEBUG supabase_url={url!r} key_len={len(key)} key_role={role!r}",
            file=sys.stderr,
            flush=True,
        )
        _client = create_client(url, key)
    return _client
