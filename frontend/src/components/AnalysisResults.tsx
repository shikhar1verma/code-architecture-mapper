'use client';

import { AnalysisResult, DiagramMode, DiagramOption } from '@/types';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs';
import { MarkdownRenderer } from '@/components/MarkdownRenderer';
import { MermaidDiagram } from '@/components/MermaidDiagram';
import { FilesTable } from '@/components/FilesTable';
import { ComponentsView } from '@/components/ComponentsView';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Download, FileText, GitBranch, Code2, BarChart3, Eye, Zap, Settings, AlertCircle, Image as ImageIcon } from 'lucide-react';
import { useState } from 'react';
import { generateDiagramOnDemand, retryMermaidDiagram } from '@/lib/api';

interface AnalysisResultsProps {
  result: AnalysisResult;
  analysisId: string;
}

const DIAGRAM_OPTIONS: DiagramOption[] = [
  {
    mode: 'simple',
    label: 'Overview',
    description: 'High-level architecture with major component groups',
    diagram_key: 'mermaid_modules_simple'
  },
  {
    mode: 'balanced',
    label: 'Grouped',
    description: 'Organized modules with categorized dependencies',
    diagram_key: 'mermaid_modules_balanced'
  },
  {
    mode: 'detailed',
    label: 'Detailed',
    description: 'Individual modules and their relationships',
    diagram_key: 'mermaid_modules_detailed'
  },
  {
    mode: 'folders',
    label: 'Structure',
    description: 'Project folder hierarchy',
    diagram_key: 'mermaid_folders'
  }
];

export function AnalysisResults({ result, analysisId }: AnalysisResultsProps) {
  const [selectedDiagramMode, setSelectedDiagramMode] = useState<DiagramMode>('balanced');
  const [generatedDiagrams, setGeneratedDiagrams] = useState<Record<string, string>>({});
  const [loadingDiagrams, setLoadingDiagrams] = useState<Record<string, boolean>>({});
  const [diagramMessages, setDiagramMessages] = useState<Record<string, string>>({});
  const [retryingDiagrams, setRetryingDiagrams] = useState<Record<string, boolean>>({});
  const [downloadSVG, setDownloadSVG] = useState<(() => void) | null>(null);
  const [downloadPNG, setDownloadPNG] = useState<(() => void) | null>(null);
  
  // const analysisId = getAnalysisId(result); // This line is removed as analysisId is now a prop

  // Function to generate diagram on-demand
  const generateDiagram = async (mode: DiagramMode) => {
    if (mode === 'folders') {
      return; // Folders diagram is static and always available
    }
    
    if (loadingDiagrams[mode] || generatedDiagrams[mode]) {
      return; // Already loading or generated
    }
    
    setLoadingDiagrams(prev => ({ ...prev, [mode]: true }));
    
    try {
      const response = await generateDiagramOnDemand(analysisId, mode);
      setGeneratedDiagrams(prev => ({ 
        ...prev, 
        [mode]: response.diagram 
      }));
      
      // Store any quota limitation messages
      if (response.message) {
        setDiagramMessages(prev => ({
          ...prev,
          [mode]: response.message || ''
        }));
      }
    } catch (error) {
      console.error(`Failed to generate ${mode} diagram:`, error);
      
      // Since quota exhaustion is handled at the analysis level, 
      // this should mainly handle other types of errors
      setDiagramMessages(prev => ({
        ...prev,
        [mode]: 'Diagram generation encountered an issue. Please try again.'
      }));
    } finally {
      setLoadingDiagrams(prev => ({ ...prev, [mode]: false }));
    }
  };

  // Handle diagram mode selection with auto-generation
  const handleDiagramModeSelect = (mode: DiagramMode) => {
    setSelectedDiagramMode(mode);
    
    // Auto-generate if needed (balanced is generated during initial analysis, but can be regenerated if missing)
    if ((mode === 'simple' || mode === 'detailed' || mode === 'balanced') && !isDiagramAvailable(mode) && !loadingDiagrams[mode]) {
      generateDiagram(mode);
    }
  };
  
  // Function to retry a broken Mermaid diagram
  const retryDiagram = async (brokenCode: string, errorMessage: string) => {
    const mode = selectedDiagramMode;
    
    if (retryingDiagrams[mode]) {
      return; // Already retrying
    }
    
    setRetryingDiagrams(prev => ({ ...prev, [mode]: true }));
    
    try {
      console.log(`🔄 Retrying ${mode} diagram with concise error:`, errorMessage.substring(0, 150));
      
      const response = await retryMermaidDiagram(analysisId, mode, {
        broken_mermaid_code: brokenCode,
        error_message: errorMessage
      });
      
      // Update the generated diagrams with the corrected version
      setGeneratedDiagrams(prev => ({ 
        ...prev, 
        [mode]: response.corrected_diagram 
      }));
      
      // Clear any previous error messages
      setDiagramMessages(prev => ({
        ...prev,
        [mode]: ''
      }));
      
      console.log(`✅ Successfully corrected ${mode} diagram`);
      
    } catch (error) {
      console.error(`Failed to retry ${mode} diagram:`, error);
      
      let errorMsg = 'Failed to correct diagram. Please try again.';
      if (error instanceof Error) {
        if (error.message === 'quota_exhausted') {
          errorMsg = 'API quota exhausted. Please try again later.';
        } else {
          errorMsg = error.message;
        }
      }
      
      setDiagramMessages(prev => ({
        ...prev,
        [mode]: errorMsg
      }));
    } finally {
      setRetryingDiagrams(prev => ({ ...prev, [mode]: false }));
    }
  };
  
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

  const handleDownloadReady = (svgDownloader: () => void, pngDownloader: () => void) => {
    setDownloadSVG(() => svgDownloader);
    setDownloadPNG(() => pngDownloader);
  };

  const getCurrentDiagram = () => {
    const option = DIAGRAM_OPTIONS.find(opt => opt.mode === selectedDiagramMode);
    if (!option) return result.artifacts.mermaid_modules || result.artifacts.mermaid_folders || '';
    
    // Check if we have a generated diagram in state first
    if (generatedDiagrams[selectedDiagramMode]) {
      return generatedDiagrams[selectedDiagramMode];
    }
    
    const diagram = result.artifacts[option.diagram_key];
    
    // Fallback logic for missing intelligent diagrams
    if (!diagram || diagram.trim() === '') {
      if (selectedDiagramMode === 'folders') {
        return result.artifacts.mermaid_folders || '';
      }
      // For intelligent modes, fallback to basic module diagram
      return result.artifacts.mermaid_modules || '';
    }
    
    return diagram;
  };
  
  const isDiagramAvailable = (mode: DiagramMode) => {
    // Check if we have it generated in state
    if (generatedDiagrams[mode]) {
      return true;
    }
    
    const option = DIAGRAM_OPTIONS.find(opt => opt.mode === mode);
    if (!option) return false;
    
    const diagram = result.artifacts[option.diagram_key];
    return diagram && diagram.trim() !== '';
  };

  const isDiagramLoading = (mode: DiagramMode) => {
    return loadingDiagrams[mode] || false;
  };

  const getCurrentDiagramTitle = () => {
    const option = DIAGRAM_OPTIONS.find(opt => opt.mode === selectedDiagramMode);
    return option ? option.label : 'Module Dependencies';
  };

  const getDiagramIcon = (mode: DiagramMode) => {
    switch (mode) {
      case 'simple': return <Eye className="w-4 h-4" />;
      case 'balanced': return <Zap className="w-4 h-4" />;
      case 'detailed': return <Settings className="w-4 h-4" />;
      case 'folders': return <GitBranch className="w-4 h-4" />;
      default: return <GitBranch className="w-4 h-4" />;
    }
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

        {/* Dependency Summary */}
        {result.metrics.dependency_analysis && (
          <div className="mt-4">
            <span className="font-medium">Dependencies:</span>
            <div className="flex flex-wrap gap-2 mt-1">
              <Badge variant="outline" className="text-green-700 bg-green-50">
                Internal: {result.metrics.dependency_analysis.summary.internal_count}
              </Badge>
              <Badge variant="outline" className="text-blue-700 bg-blue-50">
                External: {result.metrics.dependency_analysis.summary.external_count}
              </Badge>
              <Badge variant="outline" className="text-purple-700 bg-purple-50">
                Categories: {result.metrics.dependency_analysis.summary.categories.length}
              </Badge>
            </div>
          </div>
        )}
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
            Dependencies
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
          <ComponentsView components={result.components} />
        </TabsContent>

        <TabsContent value="diagrams">
          <div className="space-y-6">
            {/* Diagram Mode Selector */}
            <Card className="p-4">
              <h3 className="text-lg font-semibold mb-3 text-gray-900">Intelligent Dependency Visualization</h3>
              <p className="text-sm text-gray-600 mb-4">
                Choose the visualization complexity that best suits your needs. Our intelligent system filters and groups dependencies for optimal clarity.
              </p>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {DIAGRAM_OPTIONS.map((option) => {
                  const isAvailable = isDiagramAvailable(option.mode);
                  const isLoading = isDiagramLoading(option.mode);
                  const isSelected = selectedDiagramMode === option.mode;
                  
                  return (
                    <button
                      key={option.mode}
                      onClick={() => handleDiagramModeSelect(option.mode)}
                      disabled={isLoading}
                      className={`p-3 rounded-lg border text-left transition-all ${
                        isSelected
                          ? 'border-blue-500 bg-blue-50 text-blue-900'
                          : isAvailable || option.mode === 'folders'
                          ? 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      } ${isLoading ? 'cursor-not-allowed opacity-75' : ''}`}
                    >
                      <div className="flex items-center mb-2">
                        {getDiagramIcon(option.mode)}
                        <span className="ml-2 font-medium text-sm">
                          {option.label}
                          {isLoading && (
                            <span className="ml-1 text-xs">(Generating...)</span>
                          )}
                          {!isAvailable && !isLoading && option.mode !== 'folders' && (
                            <span className="ml-1 text-xs">(Click to generate)</span>
                          )}
                        </span>
                      </div>
                      <p className="text-xs text-gray-600">{option.description}</p>
                    </button>
                  );
                })}
              </div>
            </Card>

            {/* Current Diagram */}
            <div>
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  {getCurrentDiagramTitle()} Dependencies
                </h3>
                <div className="flex gap-2">
                  <Button
                    onClick={() => downloadMermaid(getCurrentDiagram(), `dependencies-${selectedDiagramMode}.mmd`)}
                    variant="outline"
                    size="sm"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Mermaid
                  </Button>
                  <Button
                    onClick={downloadSVG || (() => {})}
                    variant="outline"
                    size="sm"
                    disabled={!downloadSVG}
                    className="text-orange-600 border-orange-300 hover:bg-orange-50 disabled:opacity-50"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    SVG
                  </Button>
                  <Button
                    onClick={downloadPNG || (() => {})}
                    variant="outline"
                    size="sm"
                    disabled={!downloadPNG}
                    className="text-orange-600 border-orange-300 hover:bg-orange-50 disabled:opacity-50"
                  >
                    <ImageIcon className="w-4 h-4 mr-2" />
                    PNG
                  </Button>
                </div>
              </div>
              {getCurrentDiagram() ? (
                <>
                  <MermaidDiagram 
                    key={`dependencies-${selectedDiagramMode}-${getCurrentDiagram().length}`}
                    chart={getCurrentDiagram()} 
                    id={`dependencies-${selectedDiagramMode}`} 
                    onRetry={retryDiagram}
                    onDownloadReady={handleDownloadReady}
                  />
                  {/* Show quota limitation message if available */}
                  {diagramMessages[selectedDiagramMode] && (
                    <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <div className="flex items-center">
                        <AlertCircle className="w-4 h-4 text-yellow-500 mr-2 flex-shrink-0" />
                        <p className="text-sm text-yellow-700">
                          {diagramMessages[selectedDiagramMode]}
                        </p>
                      </div>
                    </div>
                  )}
                </>
              ) : isDiagramLoading(selectedDiagramMode) ? (
                <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      Generating {getCurrentDiagramTitle()} Diagram
                    </h3>
                    <p className="text-sm text-gray-500">
                      The intelligent dependency analysis is being processed...
                    </p>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                  <div className="text-center">
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      {getCurrentDiagramTitle()} Diagram
                    </h3>
                    <p className="text-sm text-gray-500">
                      Click the &ldquo;{getCurrentDiagramTitle()}&rdquo; option above to generate this diagram.
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Dependency Insights */}
            {result.metrics.dependency_analysis && (
              <Card className="p-4">
                <h4 className="text-md font-semibold mb-3 text-gray-900">Dependency Insights</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">Internal Connections:</span>
                    <p className="text-gray-600">
                      {result.metrics.dependency_analysis.summary.internal_count} file-to-file relationships
                    </p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">External Categories:</span>
                    <p className="text-gray-600">
                      {result.metrics.dependency_analysis.summary.categories.join(', ')}
                    </p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Total Dependencies:</span>
                    <p className="text-gray-600">
                      {result.metrics.dependency_analysis.summary.external_count} external packages
                    </p>
                  </div>
                </div>
              </Card>
            )}
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