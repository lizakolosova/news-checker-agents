import { useState, useCallback} from 'react';

import { API_CONFIG, PIPELINE_STEPS, INPUT_CONSTRAINTS} from '../config/constants';

import {factCheckService} from '../services/factCheckService';

export const useFactCheck = () => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [currentStep, setCurrentStep] = useState(0);

  const factCheck = useCallback(async (articleTitle, articleText, maxClaims) => {
    if (!articleText?.trim()) {
      setError('Please enter article text');
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);
    setCurrentStep(0);

    const stepInterval = setInterval(() => {
      setCurrentStep(prev => Math.min(prev + 1, PIPELINE_STEPS.length - 1));
    }, API_CONFIG.STEP_INTERVAL_MS);

    const safeMaxClaims = Math.max(
      INPUT_CONSTRAINTS.MIN_CLAIMS,
      Number(maxClaims) || INPUT_CONSTRAINTS.DEFAULT_CLAIMS
    );

    try {
      const data = await factCheckService.checkArticle({
        article_id: `article_${Date.now()}`,
        title: articleTitle || 'Untitled Article',
        text: articleText,
        max_claims: safeMaxClaims,
      });

      clearInterval(stepInterval);
      setResults(data);
      setCurrentStep(PIPELINE_STEPS.length);
    } catch (err) {
      clearInterval(stepInterval);
      setError(
        err.message ||
        'Failed to fact-check article. Make sure the backend is running on http://localhost:8000'
      );
      console.error('Fact-check error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    loading,
    results,
    error,
    currentStep,
    factCheck,
  };
};