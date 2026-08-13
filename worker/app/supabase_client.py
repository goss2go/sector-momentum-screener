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
        # TEMPORARY DIAGNOSTIC -- remove once the "Invalid API key" issue
        # is resolved. Prints shape/length info only, never the full key.
        print(
            f"DEBUG supabase_url={url!r} "
            f"key_len={len(key)} key_repr={key[:8]!r}...{key[-8:]!r}",
            file=sys.stderr,
            flush=True,
        )
        _client = create_client(url, key)
    return _client
