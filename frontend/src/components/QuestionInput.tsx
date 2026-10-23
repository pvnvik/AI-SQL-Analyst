import React from 'react';
import { Sparkles, Loader2, ArrowRight } from 'lucide-react';

interface QuestionInputProps {
  question: string;
  setQuestion: (q: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  loading: boolean;
  disabled?: boolean;
  exampleQuestions: string[];
}

export const QuestionInput: React.FC<QuestionInputProps> = ({
  question,
  setQuestion,
  onSubmit,
  loading,
  disabled = false,
  exampleQuestions,
}) => {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
      <form onSubmit={onSubmit} className="space-y-3">
        <label htmlFor="question-input" className="block text-sm font-semibold text-slate-800">
          Ask a question about the database
        </label>
        <div className="relative">
          <textarea
            id="question-input"
            rows={3}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. Which five products generated the most revenue last quarter?"
            disabled={loading || disabled}
            className="w-full px-4 py-3 text-slate-900 placeholder-slate-400 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm resize-none disabled:bg-slate-50 transition-all"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                onSubmit(e);
              }
            }}
          />
          <div className="absolute right-3 bottom-3 flex items-center space-x-2">
            <button
              type="submit"
              disabled={!question.trim() || loading || disabled}
              className="inline-flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 text-white font-medium text-xs rounded-lg transition-colors shadow-xs"
            >
              {loading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Analyzing...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Analyze</span>
                  <ArrowRight className="w-3.5 h-3.5 ml-0.5" />
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Clickable Example Questions */}
      <div className="pt-2 border-t border-slate-100">
        <span className="text-xs font-medium text-slate-500 mr-2">Example questions:</span>
        <div className="mt-2 flex flex-wrap gap-2">
          {exampleQuestions.map((eq, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => setQuestion(eq)}
              disabled={loading}
              className="text-xs px-2.5 py-1 bg-slate-100 hover:bg-blue-50 hover:text-blue-700 text-slate-600 rounded-md transition-colors border border-slate-200 text-left"
            >
              {eq}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
