"""
Supabase client for the worker. Uses the SERVICE ROLE key, never the
anon key -- the worker needs to write rows on behalf of a user without
being subject to RLS insert policies (there are none defined for the
score/candidate tables; see the migration). Keep SUPABASE_SERVICE_ROLE_KEY
out of the Next.js app entirely -- it only ever lives in the worker's
environment.
"""

import os
from supabase import create_client, Client

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
        _client = create_client(url, key)
    return _client
