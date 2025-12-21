import {CheckCircle} from "lucide-react";
import { Sparkles } from 'lucide-react';

const Header = () => {
  return (
    <header className="sticky top-0 z-50 backdrop-blur-xl bg-white bg-opacity-80 border-b border-slate-200 shadow-sm">
      <div className="max-w-6xl mx-auto px-6 py-5">
        <div className="flex items-center gap-4">
          <div className="relative">
            <div
              className="absolute inset-0 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl blur opacity-50"
              aria-hidden="true"
            />
            <div className="relative flex items-center justify-center w-14 h-14 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl shadow-lg">
              <CheckCircle className="w-8 h-8 text-white" strokeWidth={2.5} aria-hidden="true" />
            </div>
          </div>
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-900 via-blue-900 to-indigo-900 bg-clip-text text-transparent">
              Multi-Agent Fact Checker
            </h1>
            <p className="text-sm text-slate-600 mt-1 flex items-center gap-2">
              <Sparkles className="w-3.5 h-3.5" aria-hidden="true" />
              4-Agent Pipeline: Extract → Research → Evaluate → Verdict
            </p>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;