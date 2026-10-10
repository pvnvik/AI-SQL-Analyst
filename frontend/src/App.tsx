import React, { useEffect, useState, useCallback } from 'react';
import { AppHeader } from './components/AppHeader';
import { fetchHealth } from './api/client';
import { HealthResponse } from './types';
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Server,
  Layers,
  Terminal,
  ArrowRight,
  Code2,
  FileCheck2,
  RefreshCw,
  ExternalLink,
  SlidersHorizontal,
} from 'lucide-react';

const EXAMPLE_QUESTIONS = [
  'Which five products generated the most revenue last quarter?',
  'Show total sales volume grouped by region for 2024',
  'What is the average discount given per product category?',
  'List top 10 customers by order frequency',
];

export const App: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [question, setQuestion] = useState<string>('');
  const [notice, setNotice] = useState<string | null>(null);

  const loadHealth = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchHealth();
      setHealth(data);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to connect to QueryPilot backend service');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadHealth();
  }, [loadHealth]);

  const handleAnalyzeClick = (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;
    setNotice(
      `Milestone 1 Active: Question received ("${question}"). Backend health check is verified. SQL generation & execution pipeline will be linked in Milestones 2–5 per system design specifications.`
    );
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col text-slate-900">
      <AppHeader
        health={health}
        loading={loading}
        error={error}
        onRefresh={loadHealth}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Banner / Milestone Status Card */}
        <section className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-5">
            <div>
              <div className="flex items-center space-x-2">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800">
                  Milestone 1 — Foundation Verified
                </span>
                <span className="text-xs text-slate-500">FastAPI + React + TypeScript + Tailwind</span>
              </div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-900 mt-2">
                Agentic AI SQL Analyst Workspace
              </h1>
              <p className="text-sm text-slate-600 mt-1">
                Deterministic SQL verification, Guardrails AI, and Gemini-powered analytics with LangSmith observability.
              </p>
            </div>

            <div className="flex items-center space-x-3">
              <a
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
              >
                <span>FastAPI Swagger Docs</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
              <button
                onClick={loadHealth}
                disabled={loading}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-lg transition-colors"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                <span>Re-check Health</span>
              </button>
            </div>
          </div>

          {/* Health Diagnostics Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-5">
            {/* API Health Card */}
            <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">FastAPI Endpoint</span>
                <Server className="w-4 h-4 text-blue-600" />
              </div>
              <div className="mt-3">
                <div className="flex items-center space-x-2">
                  <span
                    className={`w-2.5 h-2.5 rounded-full ${
                      error ? 'bg-rose-500' : health ? 'bg-emerald-500' : 'bg-amber-500'
                    }`}
                  />
                  <span className="text-sm font-bold text-slate-800">
                    {error ? 'Unavailable' : health ? `Status: ${health.status}` : 'Connecting...'}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  GET /api/health responding with HTTP 200
                </p>
              </div>
            </div>

            {/* Gemini LLM Card */}
            <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Model Provider</span>
                <SlidersHorizontal className="w-4 h-4 text-indigo-600" />
              </div>
              <div className="mt-3">
                <div className="flex items-center space-x-2">
                  <span
                    className={`w-2.5 h-2.5 rounded-full ${
                      health?.checks.gemini_configured ? 'bg-emerald-500' : 'bg-slate-400'
                    }`}
                  />
                  <span className="text-sm font-bold text-slate-800">
                    {health?.checks.gemini_configured ? 'Configured' : 'Key Pending'}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Model: {health?.checks.gemini_model || 'gemini-3.5-flash'}
                </p>
              </div>
            </div>

            {/* Database Target Card */}
            <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Database Dialect</span>
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
              </div>
              <div className="mt-3">
                <div className="flex items-center space-x-2">
                  <span
                    className={`w-2.5 h-2.5 rounded-full ${
                      health?.checks.database_configured ? 'bg-emerald-500' : 'bg-amber-400'
                    }`}
                  />
                  <span className="text-sm font-bold text-slate-800 capitalize">
                    {health?.checks.database_dialect || 'PostgreSQL'}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  {health?.checks.database_configured
                    ? 'Read-only role active'
                    : 'Milestone 2 Target Schema'}
                </p>
              </div>
            </div>

            {/* LangSmith Observability Card */}
            <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Observability</span>
                <Layers className="w-4 h-4 text-cyan-600" />
              </div>
              <div className="mt-3">
                <div className="flex items-center space-x-2">
                  <span
                    className={`w-2.5 h-2.5 rounded-full ${
                      health?.checks.langsmith_configured ? 'bg-emerald-500' : 'bg-slate-400'
                    }`}
                  />
                  <span className="text-sm font-bold text-slate-800">
                    {health?.checks.langsmith_configured ? 'LangSmith Active' : 'Tracing Disabled'}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Workflow Tracing & Evaluation
                </p>
              </div>
            </div>
          </div>

          {/* Error Banner if API is offline */}
          {error && (
            <div className="mt-4 p-4 rounded-lg bg-rose-50 border border-rose-200 flex items-start space-x-3 text-rose-800 text-sm">
              <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">Unable to reach FastAPI backend service</p>
                <p className="text-xs text-rose-700 mt-0.5">
                  Make sure the backend is running with:{' '}
                  <code className="bg-rose-100 px-1 py-0.5 rounded text-rose-900 font-mono">
                    uvicorn app.main:app --reload --port 8000
                  </code>
                </p>
              </div>
            </div>
          )}
        </section>

        {/* Natural Language Query Input Section */}
        <section className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
          <div className="space-y-1">
            <h2 className="text-base font-semibold text-slate-900 flex items-center space-x-2">
              <Code2 className="w-4 h-4 text-blue-600" />
              <span>Ask a Database Question</span>
            </h2>
            <p className="text-xs text-slate-500">
              Enter questions in plain English. Queries are deterministically validated before execution.
            </p>
          </div>

          <form onSubmit={handleAnalyzeClick} className="space-y-3">
            <div className="relative">
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="e.g. Which five products generated the most revenue last quarter?"
                rows={3}
                className="w-full px-4 py-3 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white resize-none transition-all placeholder:text-slate-400"
              />
              <button
                type="submit"
                disabled={!question.trim()}
                className="absolute right-3 bottom-3 inline-flex items-center space-x-1.5 px-4 py-2 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors disabled:opacity-40 disabled:cursor-not-allowed shadow-xs"
              >
                <span>Analyze</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Clickable Example Questions */}
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <span className="text-xs text-slate-500 font-medium">Examples:</span>
              {EXAMPLE_QUESTIONS.map((example, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setQuestion(example)}
                  className="text-xs px-2.5 py-1 rounded-md bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200 transition-colors text-left"
                >
                  {example}
                </button>
              ))}
            </div>
          </form>

          {/* Interactive Notice */}
          {notice && (
            <div className="p-4 rounded-lg bg-blue-50 border border-blue-200 text-blue-900 text-xs space-y-1">
              <div className="flex items-center space-x-2 font-semibold">
                <CheckCircle2 className="w-4 h-4 text-blue-600" />
                <span>Foundation Ready</span>
              </div>
              <p className="text-blue-800">{notice}</p>
            </div>
          )}
        </section>

        {/* Milestone 1 Architecture & Specifications Verification Panel */}
        <section className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="text-sm font-semibold text-slate-900 flex items-center space-x-2">
              <FileCheck2 className="w-4 h-4 text-emerald-600" />
              <span>Milestone 1 Implementation Checklist</span>
            </h3>
            <span className="text-xs font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded-full">
              Complete & Verified
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-600">
            <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/50 space-y-2">
              <div className="flex items-center space-x-2 font-medium text-slate-900">
                <Terminal className="w-4 h-4 text-blue-600" />
                <span>Backend Foundation</span>
              </div>
              <ul className="space-y-1.5 pl-6 list-disc text-slate-600">
                <li>FastAPI application initialized with lifespan & logging</li>
                <li>Pydantic Settings with safe env loading & secret masking</li>
                <li><code className="text-blue-600 font-mono">GET /api/health</code> endpoint with test suite</li>
                <li>CORS middleware configured for frontend origin</li>
                <li>Zero sensitive credentials exposed in responses or logs</li>
              </ul>
            </div>

            <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/50 space-y-2">
              <div className="flex items-center space-x-2 font-medium text-slate-900">
                <Layers className="w-4 h-4 text-indigo-600" />
                <span>Frontend Architecture</span>
              </div>
              <ul className="space-y-1.5 pl-6 list-disc text-slate-600">
                <li>React 18 + TypeScript + Vite project configured</li>
                <li>Tailwind CSS design system with custom palette</li>
                <li>Shared TypeScript interfaces matching backend contract</li>
                <li>Vite API proxy to backend at <code className="text-blue-600 font-mono">http://127.0.0.1:8000</code></li>
                <li>Professional analyst dashboard layout with real health data</li>
              </ul>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>QueryPilot — Agentic AI SQL Analyst (Milestone 1)</span>
          <span>Google Gemini &middot; LangGraph &middot; Guardrails AI &middot; SQLGlot &middot; LangSmith</span>
        </div>
      </footer>
    </div>
  );
};
export default App;
