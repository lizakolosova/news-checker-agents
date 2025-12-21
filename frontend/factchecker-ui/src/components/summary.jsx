import { useMemo } from 'react';
import { Sparkles } from 'lucide-react';

const ResultsSummary = ({ results }) => {
  const verifiedCount = useMemo(() => {
    return results.verdicts?.filter(
      v => v.rating === 'true' || v.rating === 'mostly_true'
    ).length || 0;
  }, [results.verdicts]);

  const processingTime = useMemo(() => {
    return results.duration_ms
      ? `${(results.duration_ms / 1000).toFixed(1)}s`
      : 'N/A';
  }, [results.duration_ms]);

  return (
    <section
      className="relative overflow-hidden bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-600 rounded-3xl shadow-2xl p-8 text-white"
      aria-labelledby="summary-title"
    >
      <div className="absolute top-0 right-0 w-64 h-64 bg-white opacity-5 rounded-full -mr-32 -mt-32" aria-hidden="true" />
      <div className="absolute bottom-0 left-0 w-48 h-48 bg-white opacity-5 rounded-full -ml-24 -mb-24" aria-hidden="true" />

      <div className="relative z-10">
        <h2 id="summary-title" className="text-2xl font-bold mb-6 flex items-center gap-2">
          <Sparkles className="w-6 h-6" aria-hidden="true" />
          {results.title || 'Analysis Complete'}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div className="bg-white bg-opacity-20 backdrop-blur-sm rounded-2xl p-5 border border-white border-opacity-30">
            <div className="text-4xl font-medium mb-2 text-black">
              {results.verdicts?.length || 0}
            </div>
            <div className="text-sm text-black font-medium">Claims Analyzed</div>
          </div>
          <div className="bg-white bg-opacity-20 backdrop-blur-sm rounded-2xl p-5 border border-white border-opacity-30">
            <div className="text-4xl font-medium mb-2 text-black">
              {processingTime}
            </div>
            <div className="text-sm text-black font-medium">Processing Time</div>
          </div>
          <div className="bg-white bg-opacity-20 backdrop-blur-sm rounded-2xl p-5 border border-white border-opacity-30">
            <div className="text-4xl font-medium mb-2 text-black">
              {verifiedCount}
            </div>
            <div className="text-sm text-black font-medium">Verified Claims</div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default ResultsSummary;