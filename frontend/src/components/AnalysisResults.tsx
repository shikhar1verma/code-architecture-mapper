'use client';

import { AnalysisResult } from '@/types';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs';
import { MarkdownRenderer } from '@/components/MarkdownRenderer';
import { MermaidDiagram } from '@/components/MermaidDiagram';
import { FilesTable } from '@/components/FilesTable';
import { Button } from '@/components/ui/Button';
import { Download, FileText, GitBranch, Code2, BarChart3 } from 'lucide-react';

interface AnalysisResultsProps {
  result: AnalysisResult;
}

export function AnalysisResults({ result }: AnalysisResultsProps) {
  const downloadMarkdown = () => {
    const blob = new Blob([result.artifacts.architecture_md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'Architecture.md';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const downloadMermaid = (content: string, filename: string) => {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="w-full max-w-6xl mx-auto">
      {/* Repository Info */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg border">
        <h2 className="text-xl font-semibold mb-2 text-gray-900">Repository Analysis</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="font-medium">Repository:</span>
            <p className="text-blue-600 break-all">{result.repo.url}</p>
          </div>
          <div>
            <span className="font-medium">Commit:</span>
            <p className="font-mono text-gray-600">{result.repo.commit_sha.slice(0, 8)}</p>
          </div>
          <div>
            <span className="font-medium">Total LOC:</span>
            <p>{result.loc_total.toLocaleString()}</p>
          </div>
          <div>
            <span className="font-medium">Files:</span>
            <p>{result.file_count}</p>
          </div>
        </div>
        
        {/* Language Stats */}
        <div className="mt-4">
          <span className="font-medium">Languages:</span>
          <div className="flex flex-wrap gap-2 mt-1">
            {Object.entries(result.language_stats).map(([lang, percentage]) => (
              <span
                key={lang}
                className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs"
              >
                {lang}: {percentage}%
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">
            <FileText className="w-4 h-4 mr-2" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="components">
            <Code2 className="w-4 h-4 mr-2" />
            Components
          </TabsTrigger>
          <TabsTrigger value="diagrams">
            <GitBranch className="w-4 h-4 mr-2" />
            Diagrams
          </TabsTrigger>
          <TabsTrigger value="files">
            <BarChart3 className="w-4 h-4 mr-2" />
            Files
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold text-gray-900">Architecture Overview</h3>
              <Button onClick={downloadMarkdown} variant="outline" size="sm">
                <Download className="w-4 h-4 mr-2" />
                Download MD
              </Button>
            </div>
            <MarkdownRenderer content={result.artifacts.architecture_md} />
          </div>
        </TabsContent>

        <TabsContent value="components">
          <div className="text-center py-8 text-gray-500">
            <Code2 className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>Component analysis coming soon...</p>
            <p className="text-sm">This feature will be available in future versions.</p>
          </div>
        </TabsContent>

        <TabsContent value="diagrams">
          <div className="space-y-6">
            <div>
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Module Dependencies</h3>
                <Button
                  onClick={() => downloadMermaid(result.artifacts.mermaid_modules, 'modules.mmd')}
                  variant="outline"
                  size="sm"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download
                </Button>
              </div>
              <MermaidDiagram chart={result.artifacts.mermaid_modules} id="modules" />
            </div>

            <div>
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Folder Structure</h3>
                <Button
                  onClick={() => downloadMermaid(result.artifacts.mermaid_folders, 'folders.mmd')}
                  variant="outline"
                  size="sm"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download
                </Button>
              </div>
              <MermaidDiagram chart={result.artifacts.mermaid_folders} id="folders" />
            </div>
          </div>
        </TabsContent>

        <TabsContent value="files">
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Central Files (by Degree Centrality)</h3>
            <FilesTable files={result.metrics.central_files} />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
} 