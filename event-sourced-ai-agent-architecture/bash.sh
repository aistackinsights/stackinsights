pnpm agent:replay --dataset ./eval/runs.jsonl --candidate prompt-v42
pnpm agent:score --metrics quality,cost,latency,policy
pnpm agent:gate --min-quality 0.82 --max-cost-delta 0.15 --max-policy-regressions 0
