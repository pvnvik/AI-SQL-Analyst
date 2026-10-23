import React from 'react';
import { ShieldCheck, ShieldAlert, CheckCircle2, AlertOctagon } from 'lucide-react';
import { ValidationInfo } from '../types';

interface ValidationStatusProps {
  validation: ValidationInfo;
}

export const ValidationStatus: React.FC<ValidationStatusProps> = ({ validation }) => {
  const isPassed = validation.status === 'passed';

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center space-x-2">
          {isPassed ? (
            <ShieldCheck className="w-5 h-5 text-emerald-600" />
          ) : (
            <ShieldAlert className="w-5 h-5 text-rose-600" />
          )}
          <h3 className="text-sm font-bold text-slate-800">Guardrails & Safety Status</h3>
        </div>

        <span
          className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
            isPassed
              ? 'bg-emerald-100 text-emerald-800'
              : 'bg-rose-100 text-rose-800'
          }`}
        >
          {isPassed ? 'PASSED' : validation.status.toUpperCase()}
        </span>
      </div>

      <div className="space-y-2 text-xs">
        <div className="flex items-start space-x-2">
          {isPassed ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 shrink-0" />
          ) : (
            <AlertOctagon className="w-4 h-4 text-rose-600 mt-0.5 shrink-0" />
          )}
          <span className="text-slate-600">
            {isPassed
              ? 'Query verified strictly read-only by SQLGlot AST parsing and approved schema allowlist.'
              : 'Query safety checks identified policy violations or syntax errors.'}
          </span>
        </div>

        {validation.messages && validation.messages.length > 0 && (
          <div className="mt-2 p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1">
            <span className="font-semibold text-slate-700 block">Validator Messages:</span>
            {validation.messages.map((msg, i) => (
              <p key={i} className="text-slate-600 font-mono text-[11px]">
                &bull; {msg}
              </p>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
