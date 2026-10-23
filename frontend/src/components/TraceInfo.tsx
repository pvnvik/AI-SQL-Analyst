import React from 'react';
import { Activity, ExternalLink, Hash, Info } from 'lucide-react';
import { TraceInfo as TraceInfoType } from '../types';

interface TraceInfoProps {
  requestId: string;
  trace: TraceInfoType;
}

export const TraceInfo: React.FC<TraceInfoProps> = ({ requestId, trace }) => {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center space-x-2">
          <Activity className="w-4 h-4 text-purple-600" />
          <h3 className="text-sm font-bold text-slate-800">LangSmith Observability</h3>
        </div>
        <span className="text-xs font-mono px-2 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200">
          {trace.project}
        </span>
      </div>

      <div className="space-y-3 text-xs">
        <div className="flex items-center justify-between text-slate-600">
          <span className="flex items-center space-x-1 text-slate-500">
            <Hash className="w-3.5 h-3.5" />
            <span>Request ID:</span>
          </span>
          <span className="font-mono text-slate-800 font-medium">{requestId}</span>
        </div>

        {trace.url ? (
          <a
            href={trace.url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-xs font-medium transition-colors"
          >
            <span>View Trace in LangSmith</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        ) : (
          <div className="flex items-start space-x-2 text-slate-500 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
            <Info className="w-3.5 h-3.5 text-slate-400 mt-0.5 shrink-0" />
            <span>
              Workflow execution traced under project <strong className="text-slate-700">{trace.project}</strong>. Direct trace link is active when remote LangSmith credentials are provided.
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
