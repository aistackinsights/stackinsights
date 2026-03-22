import { z } from "zod";

const planSchema = z.object({
  runId: z.string().min(8),
  maxSteps: z.number().int().min(1).max(20),
  budgetUsd: z.number().min(0.01).max(10),
  steps: z.array(
    z.object({
      id: z.string(),
      objective: z.string().min(5),
      tool: z.enum(["search_docs", "query_sql", "create_ticket", "send_email"]),
      input: z.record(z.unknown()),
      successCriteria: z.string().min(5),
    })
  ).min(1),
  stopConditions: z.array(z.string()).min(1),
});
