/**
 * QueryPilot Shared TypeScript Interfaces
 * Matches backend contracts specified in QueryPilot_System_Design.md
 */

export interface HealthChecks {
  gemini_configured: boolean;
  gemini_model: string;
  database_configured: boolean;
  database_dialect: string;
  langsmith_configured: boolean;
}

export interface HealthResponse {
  status: string;
  app_env: string;
  version: string;
  checks: HealthChecks;
}

export interface ValidationInfo {
  status: 'passed' | 'rejected_unsafe_sql' | 'rejected_invalid_sql' | 'rejected_unknown_schema_reference' | 'repair_attempted' | 'repair_limit_reached';
  messages: string[];
}

export interface ExecutionInfo {
  duration_ms: number;
  row_count: number;
  truncated: boolean;
}

export interface ChartConfig {
  type: string;
  title: string;
  x: string;
  y: string;
}

export interface TraceInfo {
  project: string;
  url: string | null;
}

export interface QueryResponse {
  request_id: string;
  question: string;
  sql: string;
  columns: string[];
  rows: Record<string, unknown>[];
  insight: string;
  chart?: ChartConfig | null;
  validation: ValidationInfo;
  execution: ExecutionInfo;
  trace: TraceInfo;
}

export interface QueryRequest {
  question: string;
}
