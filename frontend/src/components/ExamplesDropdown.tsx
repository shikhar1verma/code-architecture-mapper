'use client';

import React, { useState, useEffect } from 'react';
import { ChevronDown, GitBranch, FileText, Code2, Loader2 } from 'lucide-react';
import { fetchExamples } from '@/lib/api';
import { ExampleSummary } from '@/types';

interface ExamplesDropdownProps {
  selectedExampleId: string | null;
  onExampleSelect: (exampleId: string | null) => void;
  disabled?: boolean;
}

export function ExamplesDropdown({ 
  selectedExampleId, 
  onExampleSelect, 
  disabled = false 
}: ExamplesDropdownProps) {
  const [examples, setExamples] = useState<ExampleSummary[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load examples on component mount
  useEffect(() => {
    const loadExamples = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const examplesList = await fetchExamples();
        setExamples(examplesList);
      } catch (err) {
        console.error('Failed to load examples:', err);
        setError('Failed to load examples');
      } finally {
        setIsLoading(false);
      }
    };

    loadExamples();
  }, []);

  const selectedExample = examples.find(ex => ex.id === selectedExampleId);

  const handleExampleSelect = (exampleId: string | null) => {
    onExampleSelect(exampleId);
    setIsOpen(false);
  };

  const formatLanguageStats = (stats: Record<string, number>) => {
    const topLanguages = Object.entries(stats)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 2)
      .map(([lang]) => lang);
    return topLanguages.join(', ');
  };

  if (isLoading) {
    return (
      <div className="relative">
        <div className="w-full p-3 border border-gray-300 rounded-lg bg-gray-50 flex items-center justify-between">
          <div className="flex items-center text-gray-500">
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Loading examples...
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="relative">
        <div className="w-full p-3 border border-red-300 rounded-lg bg-red-50 text-red-700">
          ⚠️ {error}
        </div>
      </div>
    );
  }

  return (
    <div className="relative">
      {/* Dropdown Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled}
        className={`
          w-full p-3 border rounded-lg text-left flex items-center justify-between
          transition-colors duration-200
          ${disabled 
            ? 'border-gray-200 bg-gray-50 text-gray-400 cursor-not-allowed' 
            : 'border-gray-300 bg-white hover:border-blue-400 hover:bg-blue-50'
          }
          ${isOpen ? 'border-blue-500 ring-2 ring-blue-200' : ''}
        `}
      >
        <div className="flex items-center">
          <GitBranch className="w-4 h-4 mr-2 text-gray-400" />
          <span className={selectedExample ? 'text-gray-900' : 'text-gray-500'}>
            {selectedExample ? selectedExample.name : 'Choose an example'}
          </span>
        </div>
        <ChevronDown 
          className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${
            isOpen ? 'rotate-180' : ''
          }`} 
        />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-300 rounded-lg shadow-lg z-50 max-h-80 overflow-y-auto">
          {/* Clear Selection Option */}
          <button
            onClick={() => handleExampleSelect(null)}
            className="w-full p-3 text-left hover:bg-gray-50 border-b border-gray-100 flex items-center"
          >
            <div className="w-4 h-4 mr-2" /> {/* Spacer for alignment */}
            <span className="text-gray-600 italic">No example selected</span>
          </button>

          {/* Example Options */}
          {examples.map((example) => (
            <button
              key={example.id}
              onClick={() => handleExampleSelect(example.id)}
              className={`
                w-full p-3 text-left hover:bg-blue-50 transition-colors duration-150
                ${selectedExampleId === example.id ? 'bg-blue-100' : ''}
              `}
            >
              <div className="flex items-start">
                <Code2 className="w-4 h-4 mr-3 mt-0.5 text-blue-500 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-gray-900 truncate">
                    {example.name}
                  </div>
                  {example.description && (
                    <div className="text-sm text-gray-600 mt-0.5 line-clamp-2">
                      {example.description}
                    </div>
                  )}
                  <div className="flex items-center mt-1.5 text-xs text-gray-500 space-x-4">
                    <span className="flex items-center">
                      <FileText className="w-3 h-3 mr-1" />
                      {example.file_count.toLocaleString()} files
                    </span>
                    <span>
                      {example.loc_total.toLocaleString()} LOC
                    </span>
                    {example.language_stats && (
                      <span>
                        {formatLanguageStats(example.language_stats)}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Click overlay to close dropdown */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
} 