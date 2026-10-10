import React from 'react';
import { HealthResponse } from '../types';
import { Database, Sparkles, Activity, RefreshCw, CheckCircle2, AlertCircle } from 'lucide-react';

interface AppHeaderProps {
  health: HealthResponse | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
}

export const AppHeader: React.FC<AppHeaderProps> = ({
  health,
  loading,
  error,
  onRefresh,
}) => {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Branding */}
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-sm shadow-blue-500/20">
              <Database className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-lg font-bold tracking-tight text-slate-900">QueryPilot</span>
                <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-blue-50 text-blue-700 border border-blue-200">
                  v{health?.version || '0.1.0'}
                </span>
                <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-slate-100 text-slate-600 border border-slate-200">
                  {health?.app_env || 'Milestone 1'}
                </span>
              </div>
              <p className="text-xs text-slate-500 hidden sm:block">Agentic AI SQL Analyst</p>
            </div>
          </div>

          {/* System Status Indicators */}
          <div className="flex items-center space-x-2 sm:space-x-3">
            {/* API Status Badge */}
            <div
              className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-xs font-medium border transition-colors ${
                error
                  ? 'bg-rose-50 text-rose-700 border-rose-200'
                  : health
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : 'bg-amber-50 text-amber-700 border-amber-200'
              }`}
              title={error ? `Backend error: ${error}` : 'FastAPI Backend Status'}
            >
              {error ? (
                <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
              ) : health ? (
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              ) : (
                <Activity className="w-3.5 h-3.5 text-amber-600 animate-pulse" />
              )}
              <span className="hidden md:inline">API:</span>
              <span>{error ? 'Offline' : health ? 'Online' : 'Connecting'}</span>
            </div>

            {/* Gemini Model Badge */}
            <div
              className={`hidden sm:flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-xs font-medium border ${
                health?.checks.gemini_configured
                  ? 'bg-blue-50 text-blue-700 border-blue-200'
                  : 'bg-slate-100 text-slate-600 border-slate-200'
              }`}
              title={health?.checks.gemini_configured ? `Gemini Active: ${health.checks.gemini_model}` : 'Gemini Key Not Configured in .env'}
            >
              <Sparkles className="w-3.5 h-3.5 text-blue-500" />
              <span>Gemini:</span>
              <span className="font-semibold">
                {health?.checks.gemini_configured ? health.checks.gemini_model : 'Unconfigured'}
              </span>
            </div>

            {/* Database Status Badge */}
            <div
              className={`hidden md:flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-xs font-medium border ${
                health?.checks.database_configured
                  ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
                  : 'bg-slate-100 text-slate-600 border-slate-200'
              }`}
              title={health?.checks.database_configured ? `Database: ${health.checks.database_dialect}` : 'Database URL using default placeholder'}
            >
              <Database className="w-3.5 h-3.5 text-indigo-500" />
              <span>DB:</span>
              <span className="font-semibold">
                {health?.checks.database_configured ? health.checks.database_dialect : 'Pending'}
              </span>
            </div>

            {/* Refresh Button */}
            <button
              onClick={onRefresh}
              disabled={loading}
              aria-label="Refresh service health"
              className="p-1.5 rounded-md text-slate-500 hover:text-slate-800 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
