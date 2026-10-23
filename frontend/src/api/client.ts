import { DatabaseSchemaResponse, HealthResponse, QueryResponse } from '../types';

const API_BASE = '/api';

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

/**
 * Fetch service health status from FastAPI /api/health
 */
export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/health`, {
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    throw new ApiError(
      `Health check failed with HTTP ${response.status}: ${response.statusText}`,
      response.status
    );
  }

  return response.json();
}

/**
 * Fetch database schema metadata from FastAPI /api/schema
 */
export async function fetchSchema(): Promise<DatabaseSchemaResponse> {
  const response = await fetch(`${API_BASE}/schema`, {
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    throw new ApiError(
      `Schema fetch failed with HTTP ${response.status}: ${response.statusText}`,
      response.status
    );
  }

  return response.json();
}

/**
 * Submit natural-language question to FastAPI /api/query
 */
export async function submitQuery(question: string): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE}/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    let errorDetail = `Query failed with HTTP ${response.status}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // ignore json parse error
    }
    throw new ApiError(errorDetail, response.status);
  }

  return response.json();
}
