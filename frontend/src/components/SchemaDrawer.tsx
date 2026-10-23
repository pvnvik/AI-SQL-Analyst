import React, { useState } from 'react';
import { Database, ChevronDown, ChevronRight, Key, Layers, BookOpen } from 'lucide-react';
import { DatabaseSchemaResponse } from '../types';

interface SchemaDrawerProps {
  schema: DatabaseSchemaResponse | null;
  loading: boolean;
  onRefresh: () => void;
}

export const SchemaDrawer: React.FC<SchemaDrawerProps> = ({
  schema,
  loading,
  onRefresh,
}) => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [expandedTable, setExpandedTable] = useState<string | null>(null);

  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-5 py-3.5 flex items-center justify-between text-left hover:bg-slate-50 transition-colors"
      >
        <div className="flex items-center space-x-2.5">
          <Database className="w-4 h-4 text-blue-600" />
          <span className="text-sm font-bold text-slate-800">Approved Database Schema</span>
          {schema && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 font-medium border border-blue-100">
              {schema.approved_tables_count} Tables ({schema.dialect.toUpperCase()})
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2 text-xs text-slate-500">
          <span>{isOpen ? 'Hide Schema' : 'Explore Tables'}</span>
          {isOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        </div>
      </button>

      {isOpen && (
        <div className="p-5 border-t border-slate-100 bg-slate-50/50 space-y-4">
          {schema?.revenue_rule && (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs space-y-1">
              <div className="flex items-center space-x-1.5 font-bold text-amber-900">
                <BookOpen className="w-3.5 h-3.5 text-amber-700" />
                <span>Canonical Revenue Rule</span>
              </div>
              <p className="text-amber-800 whitespace-pre-line font-mono text-[11px]">
                {schema.revenue_rule}
              </p>
            </div>
          )}

          {loading ? (
            <div className="py-6 text-center text-xs text-slate-500">Loading schema metadata...</div>
          ) : !schema ? (
            <div className="py-6 text-center text-xs text-slate-500">
              Schema information unavailable.
              <button
                onClick={onRefresh}
                className="ml-2 text-blue-600 underline hover:text-blue-800"
              >
                Retry
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {schema.tables.map((tbl) => {
                const isTblExpanded = expandedTable === tbl.name;
                return (
                  <div
                    key={tbl.name}
                    className="bg-white border border-slate-200 rounded-lg p-3 text-xs space-y-2 shadow-2xs"
                  >
                    <div
                      onClick={() => setExpandedTable(isTblExpanded ? null : tbl.name)}
                      className="flex items-center justify-between cursor-pointer font-semibold text-slate-800"
                    >
                      <div className="flex items-center space-x-1.5">
                        <Layers className="w-3.5 h-3.5 text-slate-500" />
                        <span className="font-mono text-blue-700">{tbl.name}</span>
                        <span className="text-slate-400 font-normal">({tbl.columns.length} cols)</span>
                      </div>
                      {isTblExpanded ? (
                        <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                      ) : (
                        <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                      )}
                    </div>

                    {tbl.description && (
                      <p className="text-slate-500 text-[11px]">{tbl.description}</p>
                    )}

                    {isTblExpanded && (
                      <div className="pt-2 border-t border-slate-100 space-y-1 font-mono text-[11px]">
                        {tbl.columns.map((col) => (
                          <div
                            key={col.name}
                            className="flex items-center justify-between py-0.5 text-slate-600"
                          >
                            <span className="flex items-center space-x-1">
                              {col.primary_key && <Key className="w-2.5 h-2.5 text-amber-500" />}
                              <span className={col.primary_key ? 'font-bold text-slate-800' : ''}>
                                {col.name}
                              </span>
                            </span>
                            <span className="text-slate-400 text-[10px]">{col.type}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
