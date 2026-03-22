create table agent_events (
  run_id text not null,
  seq bigint not null,
  event_type text not null,
  event_time timestamptz not null default now(),
  actor text not null, -- orchestrator, planner, tool_executor, policy_guard
  payload jsonb not null,
  primary key (run_id, seq)
);

create index idx_agent_events_type_time
  on agent_events(event_type, event_time desc);
