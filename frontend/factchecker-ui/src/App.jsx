import { useCallback, useState } from 'react';
import { INPUT_CONSTRAINTS } from './config/constants.js';
import { useFactCheck } from './hooks/useFactCheck.js';

import Header from './components/header.jsx';
import Footer from './components/footer.jsx';
import ArticleInput from './components/input.jsx';
import { ErrorState, LoadingState } from './components/state.jsx';
import ResultsSummary from './components/summary.jsx';
import VerdictCard from './components/card.jsx';

const FactCheckerUI = () => {
  const [articleText, setArticleText] = useState('');
  const [articleTitle, setArticleTitle] = useState('');
  const [maxClaims, setMaxClaims] = useState(INPUT_CONSTRAINTS.DEFAULT_CLAIMS);

  const { loading, results, error, currentStep, factCheck } = useFactCheck();

  const handleTitleChange = useCallback((value) => {
    setArticleTitle(value);
  }, []);

  const handleTextChange = useCallback((value) => {
    setArticleText(value);
  }, []);

  const handleMaxClaimsChange = useCallback((value) => {
    setMaxClaims(value);
  }, []);

  const handleFactCheck = useCallback(() => {
    factCheck(articleTitle, articleText, maxClaims);
  }, [articleTitle, articleText, maxClaims, factCheck]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <Header />

      <main className="max-w-6xl mx-auto px-6 py-10">
        <ArticleInput
          articleTitle={articleTitle}
          onTitleChange={handleTitleChange}
          articleText={articleText}
          onTextChange={handleTextChange}
          maxClaims={maxClaims}
          onMaxClaimsChange={handleMaxClaimsChange}
          loading={loading}
          onSubmit={handleFactCheck}
        />

        {loading && <LoadingState currentStep={currentStep} />}

        <ErrorState error={error} />

        {results && (
          <div className="space-y-6">
            <ResultsSummary results={results} />

            {results.verdicts?.map((verdict, idx) => (
              <VerdictCard
                key={verdict.claim_id || idx}
                verdict={verdict}
                index={idx}
              />
            ))}
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
};

export default FactCheckerUI;
