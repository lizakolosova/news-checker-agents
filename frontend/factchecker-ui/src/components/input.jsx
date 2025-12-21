import {useCallback} from "react";
import {EXAMPLE_ARTICLES, INPUT_CONSTRAINTS} from "../config/constants.ts";
import { FileText, Search, Loader } from 'lucide-react';

const ArticleInput = ({
  articleTitle,
  onTitleChange,
  articleText,
  onTextChange,
  maxClaims,
  onMaxClaimsChange,
  loading,
  onSubmit,
}) => {
  const handleExampleClick = useCallback((example) => {
    onTitleChange(example.title);
    onTextChange(example.text);
  }, [onTitleChange, onTextChange]);

  const handleSubmit = useCallback((e) => {
    e.preventDefault();
    onSubmit();
  }, [onSubmit]);

  const isSubmitDisabled = loading || !articleText?.trim();

  return (
    <section
      className="bg-white rounded-3xl shadow-xl border border-slate-200 overflow-hidden mb-8"
      aria-labelledby="input-section-title"
    >
      <div className="bg-gradient-to-r from-slate-50 to-blue-50 px-8 py-6 border-b border-slate-200">
        <h2
          id="input-section-title"
          className="text-xl font-bold text-slate-900 flex items-center gap-3"
        >
          <div className="p-2 bg-blue-100 rounded-lg" aria-hidden="true">
            <FileText className="w-5 h-5 text-blue-600" />
          </div>
          Article Input
        </h2>
      </div>

      <div className="p-8">
        <div className="mb-6">
          <label className="text-sm font-semibold text-slate-700 mb-3 block">
            Quick Examples
          </label>
          <div className="flex flex-wrap gap-3" role="group" aria-label="Example articles">
            {EXAMPLE_ARTICLES.map((example, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleExampleClick(example)}
                className="group relative px-5 py-2.5 bg-gradient-to-r from-blue-50 to-indigo-50 text-blue-700 rounded-xl font-medium hover:from-blue-100 hover:to-indigo-100 transition-all shadow-sm hover:shadow-md border border-blue-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                aria-label={`Load example: ${example.title}`}
              >
                <span className="relative z-10">{example.title}</span>
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label
              htmlFor="article-title"
              className="text-sm font-semibold text-slate-700 mb-2 block"
            >
              Article Title (Optional)
            </label>
            <input
              id="article-title"
              type="text"
              placeholder="Enter article title..."
              value={articleTitle}
              onChange={(e) => onTitleChange(e.target.value)}
              className="w-full px-4 py-3.5 border-2 border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all text-slate-900 placeholder-slate-400"
            />
          </div>

          <div>
            <label
              htmlFor="article-text"
              className="text-sm font-semibold text-slate-700 mb-2 block"
            >
              Article Text
            </label>
            <textarea
              id="article-text"
              placeholder="Paste your article text here..."
              value={articleText}
              onChange={(e) => onTextChange(e.target.value)}
              rows={10}
              required
              className="w-full px-4 py-3.5 border-2 border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all resize-y text-slate-900 placeholder-slate-400 font-mono text-sm leading-relaxed"
              aria-describedby="article-text-hint"
            />
            <p id="article-text-hint" className="sr-only">
              Paste the article text you want to fact-check
            </p>
          </div>

          <div className="flex items-end gap-4">
            <div className="flex-1">
              <label
                htmlFor="max-claims"
                className="text-sm font-semibold text-slate-700 mb-2 block"
              >
                Maximum Claims
              </label>
              <input
                id="max-claims"
                type="number"
                min={INPUT_CONSTRAINTS.MIN_CLAIMS}
                max={INPUT_CONSTRAINTS.MAX_CLAIMS}
                value={maxClaims}
                onChange={(e) => onMaxClaimsChange(parseInt(e.target.value) || INPUT_CONSTRAINTS.DEFAULT_CLAIMS)}
                className="w-full px-4 py-3.5 border-2 border-slate-200 rounded-xl outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all text-slate-900"
                aria-describedby="max-claims-hint"
              />
              <p id="max-claims-hint" className="sr-only">
                Number of claims to analyze (1-10)
              </p>
            </div>

            <button
              type="submit"
              disabled={isSubmitDisabled}
              className="px-8 py-3.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl font-semibold hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transition-all flex items-center gap-2.5 disabled:shadow-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              aria-label={loading ? 'Analyzing article...' : 'Start fact check'}
            >
              {loading ? (
                <>
                  <Loader className="w-5 h-5 animate-spin" aria-hidden="true" />
                  <span>Analyzing...</span>
                </>
              ) : (
                <>
                  <Search className="w-5 h-5" aria-hidden="true" />
                  <span>Fact Check</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </section>
  );
};

export default ArticleInput;