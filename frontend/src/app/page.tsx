'use client';

import { useState } from 'react';
import { UrlInput } from '@/components/UrlInput';
import { AnalysisResults } from '@/components/AnalysisResults';
import { ExamplesDropdown } from '@/components/ExamplesDropdown';
import { startAnalysis, getAnalysis, fetchExampleData, refreshAnalysis } from '@/lib/api';
import { AnalysisResult } from '@/types';
import { AlertCircle, CheckCircle2, RefreshCw, Loader2 } from 'lucide-react';
import { usePolling } from '@/hooks/usePolling';

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [selectedExampleId, setSelectedExampleId] = useState<string | null>(null);
  const [quotaExhausted, setQuotaExhausted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isShowingExample, setIsShowingExample] = useState(false);
  const [isCachedResult, setIsCachedResult] = useState(false);
  const [cachedAt, setCachedAt] = useState<string | null>(null);
  const [currentRepoUrl, setCurrentRepoUrl] = useState<string | null>(null);

  // Polling hook for async analysis
  const { status: pollingStatus, isPolling } = usePolling(
    analysisId,
    {
      onComplete: (completedResult) => {
        setResult(completedResult);
        setLoading(false);
      },
      onError: (errorMessage) => {
        setError(errorMessage);
        setLoading(false);
        setQuotaExhausted(errorMessage.includes('quota'));
      },
    }
  );

  const handleSubmit = async (url: string) => {
    setLoading(true);
    setError(null);
    setResult(null);
    setAnalysisId(null);
    setSelectedExampleId(null); // Reset example selection
    setIsShowingExample(false);
    setQuotaExhausted(false);
    setIsCachedResult(false);
    setCachedAt(null);
    setCurrentRepoUrl(url);

    try {
      const response = await startAnalysis({ repo_url: url });
      
      if (response.status === 'completed') {
        // Analysis already completed (cached) - fetch results immediately
        setAnalysisId(response.analysis_id);
        setIsCachedResult(response.cached || false);
        setCachedAt(response.cached_at || null);
        const data = await getAnalysis(response.analysis_id);
        setResult(data);
        setLoading(false);
      } else {
        // Analysis pending or started - begin polling
        setAnalysisId(response.analysis_id);
        setIsCachedResult(false);
        // Loading will be set to false when polling completes
      }
    } catch (err) {
      console.log('Error caught:', err);
      console.log('Error message:', err instanceof Error ? err.message : 'Not an Error object');
      
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      
      // Handle quota exhaustion specifically
      if (errorMessage.includes('quota_exhausted') || 
          errorMessage.includes('429') || 
          errorMessage.includes('quota')) {
        console.log('Quota exhausted detected!');
        setQuotaExhausted(true);
      } 
      // Handle other service unavailable errors
      else if (errorMessage.includes('Service temporarily unavailable')) {
        setError('The analysis service is temporarily unavailable. Please try again in a few moments.');
      }
      // Handle network/connection errors
      else if (errorMessage.includes('Failed to fetch') || errorMessage.includes('Network')) {
        setError('Unable to connect to the analysis service. Please check your internet connection and try again.');
      }
      // Handle timeout errors
      else if (errorMessage.includes('timeout')) {
        setError('The analysis is taking longer than expected. Please try again with a smaller repository or try again later.');
      }
      // General fallback for other errors
      else {
        console.log('Falling back to general error for message:', errorMessage);
        setError('An unexpected error occurred during analysis. Please try again. If the problem persists, the repository might be too large or have access restrictions.');
      }
      
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    if (!analysisId || !currentRepoUrl) return;
    
    setRefreshing(true);
    setError(null);
    setQuotaExhausted(false);

    try {
      console.log(`🔄 Refreshing analysis ${analysisId} for ${currentRepoUrl}`);
      const response = await refreshAnalysis({ repo_url: currentRepoUrl, force_refresh: true });
      
      if (response.status === 'complete') {
        // Fetch updated results
        const data = await getAnalysis(response.analysis_id);
        setResult(data);
        setIsCachedResult(false);
        setCachedAt(null);
        console.log(`✅ Refresh complete for ${currentRepoUrl}`);
      }
    } catch (err) {
      console.log('Refresh error caught:', err);
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      
      // Handle quota exhaustion specifically
      if (errorMessage.includes('quota_exhausted') || 
          errorMessage.includes('429') || 
          errorMessage.includes('quota') ||
          (err && typeof err === 'object' && 'status' in err && (err as { status: number }).status === 429)) {
        console.log('Quota exhausted during refresh!');
        setQuotaExhausted(true);
      } else {
        setError(`Failed to refresh analysis: ${errorMessage}`);
      }
    } finally {
      setRefreshing(false);
    }
  };

  const handleExampleSelect = async (exampleId: string | null) => {
    setSelectedExampleId(exampleId);
    setError(null);
    setQuotaExhausted(false);
    setIsCachedResult(false);
    setCachedAt(null);
    setCurrentRepoUrl(null);
    
    if (!exampleId) {
      // Clear selection
      setResult(null);
      setAnalysisId(null);
      setIsShowingExample(false);
      return;
    }

    setLoading(true);
    try {
      const exampleData = await fetchExampleData(exampleId);
      
      // Convert ExampleData to AnalysisResult format for compatibility
      const analysisResult: AnalysisResult = {
        status: exampleData.status,
        repo: exampleData.repo,
        language_stats: exampleData.language_stats,
        loc_total: exampleData.loc_total,
        file_count: exampleData.file_count,
        metrics: exampleData.metrics,
        components: exampleData.components,
        artifacts: exampleData.artifacts,
        token_budget: exampleData.token_budget
      };
      
      setResult(analysisResult);
      setAnalysisId(exampleId); // Use example ID as analysis ID for routing
      setIsShowingExample(true);
      
    } catch (err) {
      console.error('Failed to load example:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to load example';
      setError(errorMessage);
      setSelectedExampleId(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gray-50 pb-0">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12 pb-16">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Code Architecture Mapper
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Analyze repository architecture, understand dependencies, and visualize code relationships with AI-powered insights.
          </p>
        </div>

        {/* Quota Exhausted Message - Only show when quotas are exhausted */}
        {quotaExhausted && (
          <div className="max-w-2xl mx-auto mb-8">
            <div className="flex items-center p-4 bg-red-50 border border-red-200 rounded-lg">
              <AlertCircle className="w-5 h-5 text-red-500 mr-3 flex-shrink-0" />
              <div>
                <h3 className="text-red-800 font-medium">Demo Application - Quotas Exhausted</h3>
                <p className="text-red-700 text-sm mt-1">
                  This is a demo application using free Gemini API quotas which have been exhausted for today. Please try again tomorrow when quotas reset.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Input Section */}
        <UrlInput onSubmit={handleSubmit} loading={loading || refreshing} />

        {/* Examples Dropdown */}
        <div className="max-w-2xl mx-auto mb-8">
          <div className="mb-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Or try an example:
            </label>
          </div>
          <ExamplesDropdown
            selectedExampleId={selectedExampleId}
            onExampleSelect={handleExampleSelect}
            disabled={loading || refreshing}
          />
        </div>

        {/* Loading State */}
        {(loading || refreshing) && (
          <div className="text-center py-12">
            <div className="max-w-md mx-auto">
              {/* Main loading indicator */}
              <div className="inline-flex items-center px-6 py-4 bg-blue-50 text-blue-700 rounded-lg mb-4">
                <Loader2 className="w-5 h-5 animate-spin mr-3" />
                <div className="text-left">
                  <div className="font-medium">
                    {refreshing 
                      ? 'Refreshing analysis...'
                      : isPolling 
                        ? 'Analysis in progress...'
                        : 'Starting analysis...'
                    }
                  </div>
                  {pollingStatus?.progress_status && (
                    <div className="text-sm text-blue-600 mt-1">
                      {pollingStatus.progress_status}
                    </div>
                  )}
                </div>
              </div>
              
              {/* Sassy GenZ message for patience */}
              {isPolling && (
                <div className="text-center text-sm text-gray-600 bg-gray-50 px-4 py-3 rounded-lg">
                  <div className="font-medium text-gray-700 mb-1">
                    ✨ Hold tight, we&apos;re doing the magic! ✨
                  </div>
                  <div>
                    This usually takes around 2 minutes. Perfect time to grab that coffee you&apos;ve been putting off ☕
                    <br />
                    <span className="text-xs text-gray-500 mt-1 block">
                      (We&apos;re analyzing your code like a detective solving mysteries 🕵️‍♀️)
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="max-w-2xl mx-auto mb-8">
            <div className="flex items-center p-4 bg-red-50 border border-red-200 rounded-lg">
              <AlertCircle className="w-5 h-5 text-red-500 mr-3 flex-shrink-0" />
              <div>
                <h3 className="text-red-800 font-medium">Analysis Failed</h3>
                <p className="text-red-700 text-sm mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Success State - Only show when we have results and no quota issues */}
        {result && analysisId && !quotaExhausted && (
          <div className="mb-8">
            <div className="max-w-2xl mx-auto mb-6">
              <div className="flex items-center p-4 bg-green-50 border border-green-200 rounded-lg">
                <CheckCircle2 className="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
                <div className="flex-1">
                  <h3 className="text-green-800 font-medium">
                    {isShowingExample 
                      ? 'Example Loaded' 
                      : isCachedResult 
                        ? 'Analysis Retrieved from Cache' 
                        : 'Analysis Complete'
                    }
                  </h3>
                  <p className="text-green-700 text-sm mt-1">
                    {isShowingExample 
                      ? 'Example repository loaded successfully. View analysis below.'
                      : isCachedResult
                        ? `Previous analysis found${cachedAt ? ` (analyzed on ${new Date(cachedAt).toLocaleDateString()})` : ''}. Click refresh for latest analysis.`
                        : 'Repository analyzed successfully. View results below.'
                    }
                  </p>
                </div>
                {isCachedResult && !isShowingExample && (
                  <button
                    onClick={handleRefresh}
                    disabled={refreshing}
                    className="ml-4 inline-flex items-center px-3 py-2 text-xs font-medium text-green-700 bg-green-100 border border-green-300 rounded-md hover:bg-green-200 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {refreshing ? (
                      <>
                        <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-green-700 mr-1"></div>
                        Refreshing...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="w-3 h-3 mr-1" />
                        Refresh
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>
            
            <AnalysisResults result={result} analysisId={analysisId} />
          </div>
        )}

        {/* Help Text - Only show when no loading, no results, no errors, and no quota issues */}
        {!loading && !refreshing && !result && !error && !quotaExhausted && (
          <div className="max-w-4xl mx-auto mt-12">
            <div className="grid md:grid-cols-2 gap-8">
              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <h3 className="text-lg font-semibold mb-3 text-gray-900">What this tool does</h3>
                <ul className="space-y-2 text-gray-700">
                  <li>• Analyzes Python, TypeScript, and JavaScript codebases</li>
                  <li>• Generates architecture overview documentation</li>
                  <li>• Creates Mermaid diagrams for dependencies and structure</li>
                  <li>• Calculates file centrality and dependency metrics</li>
                  <li>• Provides downloadable reports and diagrams</li>
                </ul>
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <h3 className="text-lg font-semibold mb-3 text-gray-900">How to use</h3>
                <ol className="space-y-2 text-gray-700">
                  <li>1. Enter a public GitHub repository URL</li>
                  <li>2. Click &quot;Analyze Repository&quot; to start</li>
                  <li>3. Wait for analysis to complete</li>
                  <li>4. Explore results across different tabs</li>
                  <li>5. Download reports and diagrams as needed</li>
                </ol>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
