'use client';

import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';
import { Button } from '@/components/ui/Button';
import { RefreshCw, AlertCircle, ZoomIn, ZoomOut, RotateCcw, Copy } from 'lucide-react';

interface MermaidDiagramProps {
  chart: string;
  id?: string;
  onRetry?: (brokenCode: string, errorMessage: string) => void;
}

export function MermaidDiagram({ chart, id = 'mermaid-diagram', onRetry }: MermaidDiagramProps) {
  const ref = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [renderError, setRenderError] = useState<string | null>(null);
  const [fullErrorDetails, setFullErrorDetails] = useState<string | null>(null);
  const [conciseError, setConciseError] = useState<string | null>(null);
  const [isRetrying, setIsRetrying] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [renderKey, setRenderKey] = useState(0);

  // Extract concise error message for LLM
  const extractConciseError = (error: any): string => {
    let errorStr = '';
    if (error instanceof Error) {
      errorStr = error.message;
    } else if (typeof error === 'string') {
      errorStr = error;
    } else {
      errorStr = JSON.stringify(error);
    }

    return errorStr;
  };

  // Format error for user display (clean, editor-like)
  const formatUserError = (error: any): { message: string; details?: string } => {
    let errorStr = '';
    if (error instanceof Error) {
      errorStr = error.message;
    } else if (typeof error === 'string') {
      errorStr = error;
    } else {
      errorStr = 'Unknown rendering error';
    }
    console.log('Full error details:', errorStr);
    // Parse error with complete context (line pointer and expectations)
    const completeParseErrorMatch = errorStr.match(/Parse error on line (\d+):([\s\S]*?)-+\^([\s\S]*?)Expecting ([\s\S]*?) got ([\s\S]*?)$/m);
    if (completeParseErrorMatch) {
      const [, lineNum, context, afterPointer, expected, got] = completeParseErrorMatch;
      const cleanExpected = expected.replace(/'/g, '').trim();
      const cleanGot = got.replace(/'/g, '').trim() || 'unexpected character';
      return {
        message: `Syntax Error on line ${lineNum}`,
        details: errorStr
      };
    }

    // Parse error with line number (simpler format)
    const parseErrorMatch = errorStr.match(/Parse error on line (\d+):[\s\S]*?Expecting ([\s\S]*?) got ([\s\S]*?)"/);
    if (parseErrorMatch) {
      const [, lineNum, expected, got] = parseErrorMatch;
      return {
        message: `Syntax Error on line ${lineNum}`,
        details: errorStr
      };
    }

    // Syntax error
    const syntaxErrorMatch = errorStr.match(/Syntax error.*?(line \d+)/i);
    if (syntaxErrorMatch) {
      const [fullMatch, lineInfo] = syntaxErrorMatch;
      return {
        message: `Syntax Error (${lineInfo})`,
        details: errorStr
      };
    }

    // Generic error with line number
    const lineErrorMatch = errorStr.match(/(.*?)(line \d+)(.*)/i);
    if (lineErrorMatch) {
      const [, before, lineInfo, after] = lineErrorMatch;
      return {
        message: `Error on ${lineInfo}`,
        details: errorStr
      };
    }

    // Fallback
    return {
      message: 'Diagram Syntax Error',
      details: errorStr
    };
  };

  useEffect(() => {
    if (!ref.current || !chart) return;

    // Reset error state when chart changes
    setRenderError(null);
    setFullErrorDetails(null);
    setConciseError(null);
    setIsRetrying(false);

    // Clear any existing Mermaid cache and force fresh render
    mermaid.initialize({
      startOnLoad: false,
      theme: 'default',
      securityLevel: 'loose',
    });

    // Clear any existing SVG elements with the same ID to prevent conflicts
    const existingElements = document.querySelectorAll(`[id*="${id}"]`);
    existingElements.forEach(el => {
      if (el.id.startsWith(id) && el !== ref.current) {
        el.remove();
      }
    });

    // Create a unique ID for this render attempt
    const uniqueId = `${id}-${Date.now()}-${renderKey}`;
    
    const renderDiagram = async () => {
      try {
        // Clear any existing content first
        if (ref.current) {
          ref.current.innerHTML = '';
        }

        // Parse and render the diagram
        await mermaid.parse(chart); // Validate syntax first
        const { svg } = await mermaid.render(uniqueId, chart);
        
        if (ref.current) {
          ref.current.innerHTML = svg;
        }
      } catch (error) {
        // Extract different error formats
        const userError = formatUserError(error);
        const conciseErrorForLLM = extractConciseError(error);
        
        console.error('Mermaid rendering error:', error);
        console.log('📋 User error format:', userError);
        console.log('🤖 LLM error format:', conciseErrorForLLM);
        
        setRenderError(userError.message);
        setFullErrorDetails(userError.details || userError.message);
        setConciseError(conciseErrorForLLM);
        
        if (ref.current) {
          ref.current.innerHTML = `
            <div class="text-red-500 p-4 bg-red-50 rounded border border-red-200">
              <div class="flex items-center mb-3">
                <svg class="w-5 h-5 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                </svg>
                <span class="font-semibold">${userError.message}</span>
              </div>
              ${userError.details ? `<p class="text-sm text-red-700 mb-3">${userError.details}</p>` : ''}
              <div id="retry-button-container-${uniqueId}"></div>
            </div>
          `;
        }
      }
    };

    renderDiagram();
  }, [chart, id, renderKey]);

  const handleRetry = async () => {
    if (!onRetry || !conciseError) return;
    
    setIsRetrying(true);
    try {
      // Send only the concise error to the backend
      await onRetry(chart, conciseError);
      
      // Force a re-render by updating the render key
      setRenderKey(prev => prev + 1);
    } catch (error) {
      console.error('Retry failed:', error);
    } finally {
      setIsRetrying(false);
    }
  };

  const copyErrorDetails = () => {
    if (conciseError) {
      const copyText = `User Error: ${renderError}\nDetails: ${fullErrorDetails}\n\nTechnical Error for Debugging:\n${conciseError}`;
      navigator.clipboard.writeText(copyText);
    }
  };

  const handleZoomIn = () => {
    setZoomLevel(prev => Math.min(prev + 0.2, 3));
  };

  const handleZoomOut = () => {
    setZoomLevel(prev => Math.max(prev - 0.2, 0.5));
  };

  const handleResetZoom = () => {
    setZoomLevel(1);
  };

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -0.1 : 0.1;
    setZoomLevel(prev => Math.max(0.5, Math.min(3, prev + delta)));
  };

  return (
    <div className="w-full">
      {/* Zoom Controls */}
      <div className="mb-3 flex justify-between items-center">
        <div className="flex gap-2">
          <Button
            onClick={handleZoomIn}
            variant="outline"
            size="sm"
            className="text-blue-600 border-blue-300 hover:bg-blue-50"
          >
            <ZoomIn className="w-4 h-4 mr-1" />
            Zoom In
          </Button>
          <Button
            onClick={handleZoomOut}
            variant="outline"
            size="sm"
            className="text-blue-600 border-blue-300 hover:bg-blue-50"
          >
            <ZoomOut className="w-4 h-4 mr-1" />
            Zoom Out
          </Button>
          <Button
            onClick={handleResetZoom}
            variant="outline"
            size="sm"
            className="text-gray-600 border-gray-300 hover:bg-gray-50"
          >
            <RotateCcw className="w-4 h-4 mr-1" />
            Reset
          </Button>
        </div>
        <span className="text-sm text-gray-500">
          Zoom: {Math.round(zoomLevel * 100)}%
        </span>
      </div>

      {/* Diagram Container */}
      <div 
        ref={containerRef}
        className="w-full overflow-auto bg-white border rounded-lg cursor-grab active:cursor-grabbing"
        style={{ minHeight: '200px' }}
        onWheel={handleWheel}
      >
        <div 
          ref={ref}
          className="p-4 transition-transform duration-200 ease-out origin-top-left"
          style={{ 
            transform: `scale(${zoomLevel})`,
            transformOrigin: 'top left'
          }}
        />
      </div>

      {/* Clean Syntax Error Display */}
      {renderError && (
        <div className="mt-4 p-4 bg-red-50 border-l-4 border-red-400 rounded-r-lg">
          <div className="flex items-start justify-between">
            <div className="flex items-start">
              <AlertCircle className="w-5 h-5 text-red-500 mr-3 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h4 className="font-medium text-red-900 text-base">{renderError}</h4>
                {fullErrorDetails && fullErrorDetails !== renderError && (
                  <p className="text-sm text-red-700 mt-2 font-mono bg-red-100 p-2 rounded">
                    {fullErrorDetails}
                  </p>
                )}
              </div>
            </div>
            
            <div className="flex gap-2 ml-4">
              {conciseError && (
                <Button
                  onClick={copyErrorDetails}
                  variant="outline"
                  size="sm"
                  className="text-red-600 border-red-300 hover:bg-red-100"
                >
                  <Copy className="w-4 h-4 mr-1" />
                  Copy
                </Button>
              )}
              
              {onRetry && (
                <Button
                  onClick={handleRetry}
                  disabled={isRetrying}
                  variant="outline"
                  size="sm"
                  className="text-blue-600 border-blue-300 hover:bg-blue-50"
                >
                  {isRetrying ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Fixing...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Fix with AI
                    </>
                  )}
                </Button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 