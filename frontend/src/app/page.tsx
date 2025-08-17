'use client';

import { useState } from 'react';
import { UrlInput } from '@/components/UrlInput';
import { AnalysisResults } from '@/components/AnalysisResults';
import { startAnalysis, getAnalysis } from '@/lib/api';
import { AnalysisResult } from '@/types';
import { AlertCircle, CheckCircle2 } from 'lucide-react';

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (url: string) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await startAnalysis({ repo_url: url });
      
      if (response.status === 'complete') {
        // Since the backend is synchronous, we can immediately fetch the result
        const data = await getAnalysis(response.analysis_id);
        setResult(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Code Architecture Mapper
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Analyze GitHub repositories and visualize their architecture
          </p>
          
          <UrlInput onSubmit={handleSubmit} loading={loading} />
        </div>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-flex items-center px-4 py-2 bg-blue-50 text-blue-700 rounded-lg">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-700 mr-3"></div>
              Analyzing repository... This may take a few moments.
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

        {/* Success State */}
        {result && (
          <div className="mb-8">
            <div className="max-w-2xl mx-auto mb-6">
              <div className="flex items-center p-4 bg-green-50 border border-green-200 rounded-lg">
                <CheckCircle2 className="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
                <div>
                  <h3 className="text-green-800 font-medium">Analysis Complete</h3>
                  <p className="text-green-700 text-sm mt-1">
                    Repository analyzed successfully. View results below.
                  </p>
                </div>
              </div>
            </div>
            
            <AnalysisResults result={result} />
          </div>
        )}

        {/* Help Text */}
        {!loading && !result && !error && (
          <div className="max-w-4xl mx-auto mt-12">
            <div className="grid md:grid-cols-2 gap-8">
              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <h3 className="text-lg font-semibold mb-3">What this tool does</h3>
                <ul className="space-y-2 text-gray-600">
                  <li>• Analyzes Python, TypeScript, and JavaScript codebases</li>
                  <li>• Generates architecture overview documentation</li>
                  <li>• Creates Mermaid diagrams for dependencies and structure</li>
                  <li>• Calculates file centrality and dependency metrics</li>
                  <li>• Provides downloadable reports and diagrams</li>
                </ul>
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <h3 className="text-lg font-semibold mb-3">How to use</h3>
                <ol className="space-y-2 text-gray-600">
                  <li>1. Enter a public GitHub repository URL</li>
                  <li>2. Click "Analyze Repository" to start</li>
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
