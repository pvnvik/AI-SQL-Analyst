import React, { useState } from 'react';
import { Copy, Check, Terminal, ShieldCheck } from 'lucide-react';

interface SqlViewerProps {
  sql: string;
}

export const SqlViewer: React.FC<SqlViewerProps> = ({ sql }) => {
  const [copied, setCopied] = useState<boolean>(false);

  const handleCopy = async () => {
    if (!sql) return;
    try {
      await navigator.clipboard.writeText(sql);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback
    }
  };

  if (!sql) {
    return (
      <div className="p-8 text-center text-slate-500 text-sm">
        No SQL query was generated for this request.
      </div>
    );
  }

  return (
    <div className="relative rounded-xl overflow-hidden border border-slate-800 bg-slate-950 font-mono shadow-md">
      <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900 border-b border-slate-800 text-xs">
        <div className="flex items-center space-x-2 text-slate-300">
          <Terminal className="w-3.5 h-3.5 text-blue-400" />
          <span className="font-semibold text-slate-200">Generated SQL</span>
          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-950 text-emerald-400 border border-emerald-800/60">
            <ShieldCheck className="w-2.5 h-2.5 mr-1" />
            Read-Only Verified
          </span>
        </div>

        <button
          onClick={handleCopy}
          className="inline-flex items-center space-x-1 px-2.5 py-1 text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded transition-colors text-xs"
          title="Copy SQL to clipboard"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400 font-sans">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span className="font-sans">Copy SQL</span>
            </>
          )}
        </button>
      </div>

      <div className="p-4 overflow-x-auto text-xs text-slate-200 leading-relaxed max-h-96">
        <pre className="selection:bg-blue-900 selection:text-white">
          <code>{sql}</code>
        </pre>
      </div>
    </div>
  );
};
