import { STANCE_CONFIG } from '../config/constants.ts';
import { ExternalLink } from 'lucide-react';
import SourceBadge from './util.jsx';

const SourceItem = ({ source, index }) => {
  const stanceInfo = STANCE_CONFIG[source.stance] || STANCE_CONFIG.unclear;
  const StanceIcon = stanceInfo.icon;

  return (
    <article
      className={`flex items-start gap-4 p-5 rounded-2xl hover:shadow-md transition-all border-2 ${stanceInfo.bg} ${stanceInfo.border}`}
      aria-labelledby={`source-${index}-title`}
    >
      <div
        className={`flex-shrink-0 w-10 h-10 rounded-xl ${stanceInfo.bg} flex items-center justify-center border ${stanceInfo.border}`}
        aria-hidden="true"
      >
        <StanceIcon className={`w-5 h-5 ${stanceInfo.color}`} strokeWidth={2.5} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-3 mb-2">
          <h5 id={`source-${index}-title`} className="font-bold text-slate-900 text-sm">
            {source.title}
          </h5>
          <a
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-shrink-0 text-blue-600 hover:text-blue-800 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
            aria-label={`Open source: ${source.title} in new tab`}
          >
            <ExternalLink className="w-5 h-5" />
          </a>
        </div>
        <div className="flex items-center gap-3">
          <SourceBadge tier={source.tier} />
          <span className={`text-xs font-bold ${stanceInfo.color} uppercase`}>
            {source.stance}
          </span>
        </div>
      </div>
    </article>
  );
};

export default SourceItem;