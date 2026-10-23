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
  status: string;
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

export interface ColumnSchema {
  name: string;
  type: string;
  nullable: boolean;
  primary_key: boolean;
  foreign_key?: string | null;
}

export interface TableSchema {
  name: string;
  description: string;
  columns: ColumnSchema[];
  primary_keys: string[];
}

export interface DatabaseSchemaResponse {
  dialect: string;
  tables: TableSchema[];
  approved_tables_count: number;
  revenue_rule: string;
}
