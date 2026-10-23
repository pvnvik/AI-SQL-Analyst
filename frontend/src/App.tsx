import React, { useEffect, useState, useCallback } from 'react';
import { AppHeader } from './components/AppHeader';
import { QuestionInput } from './components/QuestionInput';
import { SqlViewer } from './components/SqlViewer';
import { ResultsTable } from './components/ResultsTable';
import { ResultsChart } from './components/ResultsChart';
import { InsightPanel } from './components/InsightPanel';
import { ValidationStatus } from './components/ValidationStatus';
import { TraceInfo } from './components/TraceInfo';
import { SchemaDrawer } from './components/SchemaDrawer';
import { fetchHealth, fetchSchema, submitQuery } from './api/client';
import { DatabaseSchemaResponse, HealthResponse, QueryResponse } from './types';
import {
  Table,
  BarChart3,
  Code2,
  ShieldCheck,
  Activity,
  AlertCircle,
} from 'lucide-react';

const EXAMPLE_QUESTIONS = [
  'Which five products generated the most revenue?',
  'How many customers are in each region?',
  'List all Electronics products sorted by unit price descending',
  'What is the total revenue and order count by product category?',
  'Show all orders placed with status shipped',
];

type ResultTab = 'data' | 'chart' | 'sql' | 'validation' | 'trace';

export const App: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [schema, setSchema] = useState<DatabaseSchemaResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState<boolean>(true);
  const [schemaLoading, setSchemaLoading] = useState<boolean>(false);
  const [healthError, setHealthError] = useState<string | null>(null);

  // Query workflow state
  const [question, setQuestion] = useState<string>('');
  const [queryLoading, setQueryLoading] = useState<boolean>(false);
  const [queryError, setQueryError] = useState<string | null>(null);
  const [currentResult, setCurrentResult] = useState<QueryResponse | null>(null);
  const [activeTab, setActiveTab] = useState<ResultTab>('data');

  // Load initial health and schema
  const loadInitialData = useCallback(async () => {
    setHealthLoading(true);
    setHealthError(null);
    try {
      const hData = await fetchHealth();
      setHealth(hData);
    } catch (err: unknown) {
      setHealthError(err instanceof Error ? err.message : 'Backend connection unavailable');
    } finally {
      setHealthLoading(false);
    }

    setSchemaLoading(true);
    try {
      const sData = await fetchSchema();
      setSchema(sData);
    } catch {
      // Schema may fail if DB not yet seeded, handled gracefully
    } finally {
      setSchemaLoading(false);
    }
  }, []);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // Handle query submission
  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanQ = question.trim();
    if (!cleanQ || queryLoading) return;

    setQueryLoading(true);
    setQueryError(null);

    try {
      const result = await submitQuery(cleanQ);
      setCurrentResult(result);
      // Auto-switch to chart if chart available, otherwise data
      if (result.chart && result.rows.length >= 2) {
        setActiveTab('chart');
      } else {
        setActiveTab('data');
      }
    } catch (err: unknown) {
      setQueryError(
        err instanceof Error ? err.message : 'An unexpected error occurred executing your question.'
      );
    } finally {
      setQueryLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col text-slate-900 font-sans">
      <AppHeader
        health={health}
        loading={healthLoading}
        error={healthError}
        onRefresh={loadInitialData}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Question Input Card */}
        <QuestionInput
          question={question}
          setQuestion={setQuestion}
          onSubmit={handleAnalyze}
          loading={queryLoading}
          exampleQuestions={EXAMPLE_QUESTIONS}
        />

        {/* Database Schema Explorer Drawer */}
        <SchemaDrawer
          schema={schema}
          loading={schemaLoading}
          onRefresh={loadInitialData}
        />

        {/* Query Execution Error Banner */}
        {queryError && (
          <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-start space-x-3 text-rose-800 text-xs shadow-xs">
            <AlertCircle className="w-4 h-4 text-rose-600 mt-0.5 shrink-0" />
            <div className="space-y-1">
              <span className="font-bold block">Execution Notice</span>
              <p>{queryError}</p>
            </div>
          </div>
        )}

        {/* Results Workspace */}
        {currentResult && (
          <div className="space-y-5 animate-in fade-in duration-300">
            {/* Top Insight Card */}
            <InsightPanel
              insight={currentResult.insight}
              execution={currentResult.execution}
              validation={currentResult.validation}
            />

            {/* Tabbed Result Inspection Panel */}
            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
              <div className="flex border-b border-slate-200 bg-slate-50/75 px-4 pt-2 gap-2 text-xs">
                <button
                  onClick={() => setActiveTab('data')}
                  className={`flex items-center space-x-1.5 py-2 px-3.5 font-semibold rounded-t-lg transition-colors border-b-2 -mb-px ${
                    activeTab === 'data'
                      ? 'border-blue-600 text-blue-700 bg-white'
                      : 'border-transparent text-slate-500 hover:text-slate-800'
                  }`}
                >
                  <Table className="w-3.5 h-3.5" />
                  <span>Data Table</span>
                  {currentResult.rows.length > 0 && (
                    <span className="ml-1 px-1.5 py-0.2 bg-slate-100 text-slate-600 rounded text-[10px]">
                      {currentResult.rows.length}
                    </span>
                  )}
                </button>

                {currentResult.chart && (
                  <button
                    onClick={() => setActiveTab('chart')}
                    className={`flex items-center space-x-1.5 py-2 px-3.5 font-semibold rounded-t-lg transition-colors border-b-2 -mb-px ${
                      activeTab === 'chart'
                        ? 'border-blue-600 text-blue-700 bg-white'
                        : 'border-transparent text-slate-500 hover:text-slate-800'
                    }`}
                  >
                    <BarChart3 className="w-3.5 h-3.5" />
                    <span>Visualization</span>
                  </button>
                )}

                <button
                  onClick={() => setActiveTab('sql')}
                  className={`flex items-center space-x-1.5 py-2 px-3.5 font-semibold rounded-t-lg transition-colors border-b-2 -mb-px ${
                    activeTab === 'sql'
                      ? 'border-blue-600 text-blue-700 bg-white'
                      : 'border-transparent text-slate-500 hover:text-slate-800'
                  }`}
                >
                  <Code2 className="w-3.5 h-3.5" />
                  <span>Generated SQL</span>
                </button>

                <button
                  onClick={() => setActiveTab('validation')}
                  className={`flex items-center space-x-1.5 py-2 px-3.5 font-semibold rounded-t-lg transition-colors border-b-2 -mb-px ${
                    activeTab === 'validation'
                      ? 'border-blue-600 text-blue-700 bg-white'
                      : 'border-transparent text-slate-500 hover:text-slate-800'
                  }`}
                >
                  <ShieldCheck className="w-3.5 h-3.5" />
                  <span>Validation & Guardrails</span>
                  <span
                    className={`ml-1 w-2 h-2 rounded-full ${
                      currentResult.validation.status === 'passed'
                        ? 'bg-emerald-500'
                        : 'bg-amber-500'
                    }`}
                  />
                </button>

                <button
                  onClick={() => setActiveTab('trace')}
                  className={`flex items-center space-x-1.5 py-2 px-3.5 font-semibold rounded-t-lg transition-colors border-b-2 -mb-px ${
                    activeTab === 'trace'
                      ? 'border-blue-600 text-blue-700 bg-white'
                      : 'border-transparent text-slate-500 hover:text-slate-800'
                  }`}
                >
                  <Activity className="w-3.5 h-3.5" />
                  <span>Observability</span>
                </button>
              </div>

              <div className="p-5">
                {activeTab === 'data' && (
                  <ResultsTable
                    columns={currentResult.columns}
                    rows={currentResult.rows}
                    rowCount={currentResult.execution.row_count}
                    truncated={currentResult.execution.truncated}
                  />
                )}

                {activeTab === 'chart' && (
                  <ResultsChart
                    chart={currentResult.chart ?? null}
                    rows={currentResult.rows}
                  />
                )}

                {activeTab === 'sql' && (
                  <SqlViewer sql={currentResult.sql} />
                )}

                {activeTab === 'validation' && (
                  <ValidationStatus validation={currentResult.validation} />
                )}

                {activeTab === 'trace' && (
                  <TraceInfo
                    requestId={currentResult.request_id}
                    trace={currentResult.trace}
                  />
                )}
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="bg-white border-t border-slate-200 py-4 text-center text-xs text-slate-500">
        <p>QueryPilot &bull; Agentic AI SQL Analyst with Deterministic Guardrails & LangSmith Tracing</p>
      </footer>
    </div>
  );
};

export default App;
