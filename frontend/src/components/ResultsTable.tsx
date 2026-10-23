import React from 'react';
import { Table as TableIcon, AlertCircle } from 'lucide-react';

interface ResultsTableProps {
  columns: string[];
  rows: Record<string, unknown>[];
  rowCount: number;
  truncated: boolean;
}

export const ResultsTable: React.FC<ResultsTableProps> = ({
  columns,
  rows,
  rowCount,
  truncated,
}) => {
  if (!rows || rows.length === 0 || !columns || columns.length === 0) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-8 text-center text-slate-500">
        <TableIcon className="w-8 h-8 text-slate-400 mx-auto mb-2" />
        <p className="text-sm font-medium">No tabular data returned</p>
        <p className="text-xs text-slate-400 mt-1">The query executed with 0 matching rows.</p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
      <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between text-xs text-slate-600">
        <div className="flex items-center space-x-2">
          <TableIcon className="w-4 h-4 text-slate-500" />
          <span className="font-semibold text-slate-700">Query Results</span>
          <span className="px-2 py-0.5 rounded-full bg-slate-200 text-slate-700 font-medium">
            {rowCount} {rowCount === 1 ? 'row' : 'rows'}
          </span>
        </div>

        {truncated && (
          <div className="flex items-center space-x-1 text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 text-xs">
            <AlertCircle className="w-3.5 h-3.5" />
            <span>Results capped to maximum row limit</span>
          </div>
        )}
      </div>

      <div className="overflow-x-auto max-h-96">
        <table className="w-full text-left text-xs border-collapse">
          <thead className="bg-slate-100/75 text-slate-700 font-semibold sticky top-0 border-b border-slate-200">
            <tr>
              <th className="py-2.5 px-3 w-12 text-slate-400 font-normal">#</th>
              {columns.map((col) => (
                <th key={col} className="py-2.5 px-4 font-semibold text-slate-800 tracking-wider">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-slate-700 font-mono">
            {rows.map((row, idx) => (
              <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                <td className="py-2 px-3 text-slate-400 font-sans text-[11px]">{idx + 1}</td>
                {columns.map((col) => {
                  const val = row[col];
                  const formatted =
                    typeof val === 'number'
                      ? Number.isInteger(val)
                        ? val.toLocaleString()
                        : val.toFixed(2)
                      : String(val ?? '');
                  return (
                    <td key={col} className="py-2 px-4 whitespace-nowrap">
                      {formatted}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
