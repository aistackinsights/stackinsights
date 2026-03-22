type PlanStep = {
  id: string;
  objective: string;
  tool: "search_docs" | "query_sql" | "create_ticket" | "send_email";
  input: Record<string, unknown>;
  successCriteria: string;
};

type AgentPlan = {
  runId: string;
  maxSteps: number;
  budgetUsd: number;
  steps: PlanStep[];
  stopConditions: string[];
};
