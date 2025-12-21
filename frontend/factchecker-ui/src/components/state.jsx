import { AlertCircle, CheckCircle, Loader } from 'lucide-react';
import { PIPELINE_STEPS } from '../config/constants.ts';


export const ErrorState = ({ error }) => {
  if (!error) return null;

  return (
    <div
      className="bg-red-50 border-2 border-red-300 rounded-2xl p-5 mb-8 shadow-lg"
      role="alert"
      aria-live="assertive"
    >
      <div className="flex items-start gap-4 text-red-800">
        <div className="p-2 bg-red-100 rounded-lg" aria-hidden="true">
          <AlertCircle className="w-5 h-5" strokeWidth={2.5} />
        </div>
        <div>
          <div className="font-bold text-lg mb-1">Error</div>
          <div className="text-sm">{error}</div>
        </div>
      </div>
    </div>
  );
};

export const LoadingState = ({ currentStep }) => {
  return (
    <section
      className="bg-white rounded-3xl shadow-xl border border-slate-200 overflow-hidden mb-8"
      aria-live="polite"
      aria-busy="true"
      aria-labelledby="loading-title"
    >
      <div className="bg-gradient-to-r from-blue-500 to-indigo-600 px-8 py-6 text-white">
        <h3 id="loading-title" className="text-xl font-bold mb-1 flex items-center gap-2">
          <Loader className="w-5 h-5 animate-spin" aria-hidden="true" />
          Running 4-Agent Pipeline
        </h3>
        <p className="text-sm text-blue-100">
          This may take 10-30 seconds depending on claim complexity
        </p>
      </div>

      <div className="p-8 space-y-4">
        {PIPELINE_STEPS.map((step, idx) => {
          const StepIcon = step.icon;
          const isActive = idx === currentStep;
          const isComplete = idx < currentStep;

          return (
            <div
              key={idx}
              className={`flex items-center gap-5 p-5 rounded-2xl transition-all border-2 ${
                isActive
                  ? 'bg-blue-50 border-blue-300 shadow-md'
                  : isComplete
                  ? 'bg-emerald-50 border-emerald-300'
                  : 'bg-slate-50 border-slate-200'
              }`}
              role="status"
              aria-label={`${step.label}: ${isComplete ? 'Complete' : isActive ? 'In progress' : 'Pending'}`}
            >
              <div
                className={`flex items-center justify-center w-12 h-12 rounded-xl shadow-sm ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : isComplete
                    ? 'bg-emerald-600 text-white'
                    : 'bg-slate-300 text-slate-600'
                }`}
                aria-hidden="true"
              >
                {isComplete ? (
                  <CheckCircle className="w-6 h-6" strokeWidth={2.5} />
                ) : (
                  <StepIcon className={`w-6 h-6 ${isActive ? 'animate-pulse' : ''}`} strokeWidth={2.5} />
                )}
              </div>
              <div className="flex-1">
                <div className="font-bold text-slate-900">{step.label}</div>
                <div className="text-sm text-slate-600 mt-0.5">{step.desc}</div>
              </div>
              {isActive && (
                <Loader className="w-6 h-6 text-blue-600 animate-spin" aria-hidden="true" />
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
};