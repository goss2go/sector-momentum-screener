-- Sector Rotation Income Scanner - initial schema
-- Runs are immutable once status = 'complete' (enforced at the app layer;
-- the worker only ever inserts, never updates rows in the score/candidate
-- tables after a run finishes).

create table if not exists scan_runs (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid not null references auth.users(id) on delete cascade,
  started_at      timestamptz not null default now(),
  completed_at    timestamptz,
  status          text not null default 'running'
                    check (status in ('running', 'complete', 'failed')),
  error_message   text,
  config_snapshot jsonb not null default '{}'::jsonb,
  risk_free_rate  numeric
);

create table if not exists sector_scores (
  id                    uuid primary key default gen_random_uuid(),
  run_id                uuid not null references scan_runs(id) on delete cascade,
  sector                text not null,
  etf                   text not null,
  rank                  int,               -- null if gated out
  passed_gate           boolean not null default false,
  rsi                   numeric,
  pct_off_52w_high      numeric,
  macd_rising           boolean,
  rel_strength_3m_pct   numeric,
  score                 numeric,           -- null if gated out
  is_top_3              boolean not null default false
);

create table if not exists symbol_scores (
  id                    uuid primary key default gen_random_uuid(),
  run_id                uuid not null references scan_runs(id) on delete cascade,
  sector                text not null,
  symbol                text not null,
  rank                  int not null,
  rsi                   numeric,
  pct_off_52w_high      numeric,
  macd_rising           boolean,
  rel_strength_3m_pct   numeric,
  score                 numeric not null
);

create table if not exists trade_candidates (
  id              uuid primary key default gen_random_uuid(),
  run_id          uuid not null references scan_runs(id) on delete cascade,
  symbol          text not null,
  sector          text not null,
  expiration      date not null,
  dte             int not null,
  spot            numeric not null,
  short_strike    numeric not null,
  long_strike     numeric not null,
  width           numeric not null,
  credit          numeric not null,
  max_loss        numeric not null,
  ror_pct         numeric not null,
  pop_pct         numeric not null,
  short_delta     numeric not null,
  short_oi        int not null,
  short_iv        numeric not null,
  in_sweet_spot   boolean not null default false
);

create index if not exists idx_scan_runs_user on scan_runs(user_id, started_at desc);
create index if not exists idx_sector_scores_run on sector_scores(run_id);
create index if not exists idx_symbol_scores_run on symbol_scores(run_id, sector);
create index if not exists idx_trade_candidates_run on trade_candidates(run_id, symbol);

-- ----------------------------------------------------------------------
-- Row Level Security -- every table scoped back to scan_runs.user_id
-- ----------------------------------------------------------------------
alter table scan_runs enable row level security;
alter table sector_scores enable row level security;
alter table symbol_scores enable row level security;
alter table trade_candidates enable row level security;

create policy "users read own runs"
  on scan_runs for select
  using (auth.uid() = user_id);

create policy "users insert own runs"
  on scan_runs for insert
  with check (auth.uid() = user_id);

-- Note: updates to scan_runs (status -> complete/failed, completed_at)
-- are performed by the worker using the Supabase service-role key, which
-- bypasses RLS -- users themselves never update a run row directly.

create policy "users read own sector scores"
  on sector_scores for select
  using (exists (
    select 1 from scan_runs
    where scan_runs.id = sector_scores.run_id
      and scan_runs.user_id = auth.uid()
  ));

create policy "users read own symbol scores"
  on symbol_scores for select
  using (exists (
    select 1 from scan_runs
    where scan_runs.id = symbol_scores.run_id
      and scan_runs.user_id = auth.uid()
  ));

create policy "users read own trade candidates"
  on trade_candidates for select
  using (exists (
    select 1 from scan_runs
    where scan_runs.id = trade_candidates.run_id
      and scan_runs.user_id = auth.uid()
  ));

-- The worker writes sector_scores / symbol_scores / trade_candidates and
-- updates scan_runs using the Supabase SERVICE ROLE key server-side,
-- which bypasses RLS entirely. No insert/update policies are needed here
-- for those tables since end users never write to them directly.
