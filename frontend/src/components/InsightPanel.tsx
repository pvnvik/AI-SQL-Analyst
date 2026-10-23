import React from 'react';
import { Sparkles, Clock, Rows3, CheckCircle2, AlertTriangle } from 'lucide-react';
import { ExecutionInfo, ValidationInfo } from '../types';

interface InsightPanelProps {
  insight: string;
  execution: ExecutionInfo;
  validation: ValidationInfo;
}

export const InsightPanel: React.FC<InsightPanelProps> = ({
  insight,
  execution,
  validation,
}) => {
  const isPassed = validation.status === 'passed';

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-5 h-5 text-amber-500" />
          <h2 className="text-base font-bold text-slate-900">Analyst Insight</h2>
        </div>

        <div className="flex items-center space-x-3 text-xs text-slate-500 font-mono">
          <div className="flex items-center space-x-1" title="Execution duration">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            <span>{execution.duration_ms} ms</span>
          </div>
          <div className="flex items-center space-x-1" title="Returned rows">
            <Rows3 className="w-3.5 h-3.5 text-slate-400" />
            <span>{execution.row_count} rows</span>
          </div>
          <div className="flex items-center space-x-1">
            {isPassed ? (
              <span className="inline-flex items-center text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded text-[11px] font-sans font-medium border border-emerald-200">
                <CheckCircle2 className="w-3 h-3 mr-1" />
                Validated Safe
              </span>
            ) : (
              <span className="inline-flex items-center text-amber-700 bg-amber-50 px-2 py-0.5 rounded text-[11px] font-sans font-medium border border-amber-200">
                <AlertTriangle className="w-3 h-3 mr-1" />
                {validation.status}
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="text-sm text-slate-800 leading-relaxed font-sans">
        {insight || 'Query completed without generating narrative insight.'}
      </div>
    </div>
  );
};
