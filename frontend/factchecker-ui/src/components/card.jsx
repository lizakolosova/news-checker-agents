import { RATING_CONFIG } from '../config/constants.ts';
import { FileText, Database } from 'lucide-react';
import SourceItem from './item.jsx';

const VerdictCard = ({ verdict, index }) => {
  const config = RATING_CONFIG[verdict.rating] || RATING_CONFIG.unverifiable;
  const RatingIcon = config.icon;
  const confidence = (verdict.confidence * 100).toFixed(0);

  return (
    <article
      className={`bg-white rounded-3xl shadow-xl border-2 ${config.border} overflow-hidden`}
      aria-labelledby={`verdict-${index}-title`}
    >
      <header className={`${config.bg} px-8 py-6 border-b-2 ${config.border}`}>
        <div className="flex items-start gap-5">
          <div
            className={`flex-shrink-0 w-14 h-14 rounded-2xl ${config.bg} border-2 ${config.border} flex items-center justify-center shadow-sm`}
            aria-hidden="true"
          >
            <RatingIcon className={`w-7 h-7 ${config.color}`} strokeWidth={2.5} />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <span
                className={`text-xs font-black ${config.color} uppercase tracking-wider px-3 py-1 rounded-full ${config.bg} border ${config.border}`}
                role="status"
              >
                {config.label}
              </span>
              <span className="text-sm text-slate-600 font-semibold">
                {confidence}% Confidence
              </span>
            </div>
            <p
              id={`verdict-${index}-title`}
              className="text-slate-900 font-semibold text-lg leading-relaxed"
            >
              {verdict.claim_text}
            </p>
          </div>
        </div>
      </header>

      <div className="p-8 space-y-6">
        <section aria-labelledby={`verdict-${index}-explanation-title`}>
          <h4
            id={`verdict-${index}-explanation-title`}
            className="text-sm font-bold text-slate-700 mb-3 flex items-center gap-2"
          >
            <FileText className="w-4 h-4" aria-hidden="true" />
            EXPLANATION
          </h4>
          <p className="text-slate-700 leading-relaxed bg-slate-50 p-5 rounded-2xl border border-slate-200">
            {verdict.explanation}
          </p>
        </section>

        {verdict.sources && verdict.sources.length > 0 && (
          <section aria-labelledby={`verdict-${index}-sources-title`}>
            <h4
              id={`verdict-${index}-sources-title`}
              className="text-sm font-bold text-slate-700 mb-4 flex items-center gap-2"
            >
              <Database className="w-4 h-4" aria-hidden="true" />
              KEY SOURCES ({verdict.sources.length})
            </h4>
            <div className="space-y-3">
              {verdict.sources.map((source, sIdx) => (
                <SourceItem key={sIdx} source={source} index={sIdx} />
              ))}
            </div>
          </section>
        )}

        {verdict.meta && Object.keys(verdict.meta).length > 0 && (
          <details className="group">
            <summary className="text-sm font-bold text-slate-700 cursor-pointer hover:text-slate-900 flex items-center gap-2 p-4 bg-slate-50 rounded-xl border border-slate-200 hover:border-slate-300 transition-all focus:outline-none focus:ring-2 focus:ring-slate-500">
              <span>TECHNICAL DETAILS</span>
              <span className="text-xs text-slate-500 font-normal">(click to expand)</span>
            </summary>
            <div className="mt-3 p-5 bg-slate-50 rounded-xl text-xs border border-slate-200">
              <div className="grid grid-cols-2 gap-3">
                {Object.entries(verdict.meta).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-slate-600 font-semibold">{key}:</span>
                    <span className="text-slate-900 font-bold">
                      {typeof value === 'number' ? value.toFixed(3) : String(value)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </details>
        )}
      </div>
    </article>
  );
};

export default VerdictCard;