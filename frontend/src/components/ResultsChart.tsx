import React, { useState } from 'react';
import { BarChart3, LineChart as LineChartIcon } from 'lucide-react';
import { ChartConfig } from '../types';

interface ResultsChartProps {
  chart: ChartConfig | null;
  rows: Record<string, unknown>[];
}

export const ResultsChart: React.FC<ResultsChartProps> = ({ chart, rows }) => {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  if (!chart || !rows || rows.length < 2) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-8 text-center text-slate-500">
        <BarChart3 className="w-8 h-8 text-slate-400 mx-auto mb-2" />
        <p className="text-sm font-medium">No chart suitable for this dataset</p>
        <p className="text-xs text-slate-400 mt-1">Charts require at least 2 rows and numeric metrics.</p>
      </div>
    );
  }

  // Extract data points
  const points = rows
    .map((r) => {
      const label = String(r[chart.x] ?? '');
      const rawVal = Number(r[chart.y]);
      const value = isNaN(rawVal) ? 0 : rawVal;
      return { label, value };
    })
    .filter((p) => p.label !== '');

  if (points.length === 0) {
    return null;
  }

  const values = points.map((p) => p.value);
  const maxVal = Math.max(...values, 1);
  const minVal = Math.min(...values, 0);

  const isLine = chart.type === 'line';

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center space-x-2">
          {isLine ? (
            <LineChartIcon className="w-4 h-4 text-blue-600" />
          ) : (
            <BarChart3 className="w-4 h-4 text-blue-600" />
          )}
          <h3 className="text-sm font-bold text-slate-800">{chart.title || 'Data Visualization'}</h3>
        </div>
        <span className="text-xs text-slate-500 font-mono">
          Y: {chart.y} &bull; X: {chart.x}
        </span>
      </div>

      {/* Interactive Bar Chart Visualization */}
      <div className="pt-4 pb-2">
        <div className="space-y-2.5 max-h-80 overflow-y-auto pr-2">
          {points.map((pt, idx) => {
            const pct = Math.max((pt.value / maxVal) * 100, 2);
            const isHovered = hoveredIdx === idx;

            return (
              <div
                key={idx}
                onMouseEnter={() => setHoveredIdx(idx)}
                onMouseLeave={() => setHoveredIdx(null)}
                className="group flex items-center space-x-3 text-xs"
              >
                <div
                  className="w-36 text-right font-medium text-slate-700 truncate"
                  title={pt.label}
                >
                  {pt.label}
                </div>

                <div className="flex-1 bg-slate-100 h-6 rounded-md overflow-hidden relative flex items-center px-2">
                  <div
                    className={`absolute left-0 top-0 bottom-0 rounded-md transition-all duration-300 ${
                      isHovered ? 'bg-blue-600' : 'bg-blue-500'
                    }`}
                    style={{ width: `${pct}%` }}
                  />
                  <span
                    className={`relative z-10 font-mono text-[11px] font-semibold transition-colors ${
                      pct > 25 ? 'text-white' : 'text-slate-700 ml-1'
                    }`}
                  >
                    {pt.value.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="flex justify-between items-center text-[11px] text-slate-400 pt-2 border-t border-slate-100 font-mono">
        <span>Min: {minVal.toLocaleString()}</span>
        <span>Max: {maxVal.toLocaleString()}</span>
      </div>
    </div>
  );
};
