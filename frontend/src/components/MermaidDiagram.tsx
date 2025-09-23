'use client';

import React, { useEffect, useRef, useState, useCallback } from 'react';
import mermaid from 'mermaid';
import { Button } from '@/components/ui/Button';
import { RefreshCw, AlertCircle, ZoomIn, ZoomOut, RotateCcw, Copy, Move, Maximize2, Target } from 'lucide-react';

interface MermaidDiagramProps {
  chart: string;
  id?: string;
  onRetry?: (brokenCode: string, errorMessage: string) => void;
  onDownloadReady?: (downloadSVG: () => void, downloadPNG: () => void) => void;
}

export function MermaidDiagram({ chart, id = 'mermaid-diagram', onRetry, onDownloadReady }: MermaidDiagramProps) {
  const ref = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [renderError, setRenderError] = useState<string | null>(null);
  const [fullErrorDetails, setFullErrorDetails] = useState<string | null>(null);
  const [conciseError, setConciseError] = useState<string | null>(null);
  const [isRetrying, setIsRetrying] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [renderKey, setRenderKey] = useState(0);
  const [panPosition, setPanPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [isMouseOverDiagram, setIsMouseOverDiagram] = useState(false);
  const [diagramDimensions, setDiagramDimensions] = useState({ width: 0, height: 0 });
  const [isAutoFitted, setIsAutoFitted] = useState(false);

  // Extract concise error message for LLM
  const extractConciseError = (error: unknown): string => {
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
  const formatUserError = (error: unknown): { message: string; details?: string } => {
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
      const [, lineNum] = completeParseErrorMatch;
      return {
        message: `Syntax Error on line ${lineNum}`,
        details: errorStr
      };
    }

    // Parse error with line number (simpler format)
    const parseErrorMatch = errorStr.match(/Parse error on line (\d+):[\s\S]*?Expecting ([\s\S]*?) got ([\s\S]*?)"/);
    if (parseErrorMatch) {
      const [, lineNum] = parseErrorMatch;
      return {
        message: `Syntax Error on line ${lineNum}`,
        details: errorStr
      };
    }

    // Syntax error
    const syntaxErrorMatch = errorStr.match(/Syntax error.*?(line \d+)/i);
    if (syntaxErrorMatch) {
      const [, lineInfo] = syntaxErrorMatch;
      return {
        message: `Syntax Error (${lineInfo})`,
        details: errorStr
      };
    }

    // Generic error with line number
    const lineErrorMatch = errorStr.match(/(.*?)(line \d+)(.*)/i);
    if (lineErrorMatch) {
      const [, , lineInfo] = lineErrorMatch;
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
      fontFamily: 'arial',
      fontSize: 14,
      // Enable proper edge label parsing
      markdownAutoWrap: false,
      htmlLabels: true,
      // Ensure edge labels are processed correctly
      flowchart: {
        htmlLabels: true,
        useMaxWidth: false,
      }
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
          
          // Auto-fit and center the diagram after rendering
          setTimeout(() => {
            autoFitAndCenter();
          }, 100); // Small delay to ensure DOM is updated
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

  // Add global mouse event listeners for better drag handling
  useEffect(() => {
    const handleGlobalMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      e.preventDefault();
      setPanPosition({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    };

    const handleGlobalMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleGlobalMouseMove);
      document.addEventListener('mouseup', handleGlobalMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleGlobalMouseMove);
      document.removeEventListener('mouseup', handleGlobalMouseUp);
    };
  }, [isDragging, dragStart]);

  // Prevent scrolling on the container itself (not needed with React events)
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    
    // Prevent any native scroll behavior on the container
    const preventContainerScroll = (e: Event) => {
      e.preventDefault();
      e.stopPropagation();
      return false;
    };
    
    container.addEventListener('scroll', preventContainerScroll);

    return () => {
      container.removeEventListener('scroll', preventContainerScroll);
    };
  }, []);

  // Prevent page scrolling when mouse is over diagram, but allow diagram zoom
  useEffect(() => {
    const preventPageWheelScroll = (e: WheelEvent) => {
      // Only prevent page scroll when mouse is over diagram AND event is outside our container
      if (isMouseOverDiagram) {
        const container = containerRef.current;
        if (container && !container.contains(e.target as Node)) {
          // This is a wheel event outside our diagram - prevent page scroll
          e.preventDefault();
          e.stopPropagation();
          return false;
        }
        // If event is on our container, let it through (our React handler will manage it)
      }
    };

    const disableKeyScroll = (e: KeyboardEvent) => {
      if (isMouseOverDiagram && (
        e.key === 'ArrowUp' || 
        e.key === 'ArrowDown' || 
        e.key === 'PageUp' || 
        e.key === 'PageDown' || 
        e.key === 'Home' || 
        e.key === 'End' ||
        e.key === ' '
      )) {
        e.preventDefault();
        e.stopPropagation();
        return false;
      }
    };

    if (isMouseOverDiagram) {
      // Prevent wheel scrolling on page but allow it on our container
      document.addEventListener('wheel', preventPageWheelScroll, { passive: false });
      document.addEventListener('keydown', disableKeyScroll);
      
      // Keep scrollbar visible but disabled
      const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;
      document.body.style.overflow = 'hidden';
      document.body.style.paddingRight = `${scrollbarWidth}px`; // Prevent layout shift
    } else {
      // Re-enable page scrolling
      document.body.style.overflow = '';
      document.body.style.paddingRight = '';
    }

    return () => {
      document.removeEventListener('wheel', preventPageWheelScroll);
      document.removeEventListener('keydown', disableKeyScroll);
      document.body.style.overflow = '';
      document.body.style.paddingRight = '';
    };
  }, [isMouseOverDiagram]);

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
    setIsAutoFitted(false);
  };

  const handleZoomOut = () => {
    setZoomLevel(prev => Math.max(prev - 0.2, 0.1));
    setIsAutoFitted(false);
  };

  const handleResetZoom = () => {
    setZoomLevel(1);
    setPanPosition({ x: 0, y: 0 });
    setIsAutoFitted(false);
  };

  const autoFitAndCenter = () => {
    if (!ref.current || !containerRef.current) return;

    const svgElement = ref.current.querySelector('svg');
    if (!svgElement) return;

    // Get the actual SVG dimensions - prefer viewBox for accuracy
    let svgWidth = 0, svgHeight = 0;
    
    const viewBox = svgElement.getAttribute('viewBox');
    if (viewBox) {
      const [, , width, height] = viewBox.split(' ').map(Number);
      svgWidth = width;
      svgHeight = height;
    } else {
      // Fallback to getBoundingClientRect
      const svgRect = svgElement.getBoundingClientRect();
      svgWidth = svgRect.width;
      svgHeight = svgRect.height;
    }
    
    const containerRect = containerRef.current.getBoundingClientRect();

    // Account for padding (we have p-4 which is 16px on each side)
    const padding = 32; // 16px * 2
    const availableWidth = containerRect.width - padding;
    const availableHeight = containerRect.height - padding;

    // Calculate the scale needed to fit the diagram
    const scaleX = availableWidth / svgWidth;
    const scaleY = availableHeight / svgHeight;
    
    // Use the smaller scale to ensure it fits in both dimensions, with some margin
    const optimalScale = Math.min(scaleX, scaleY) * 0.9; // 90% to leave some margin
    const finalScale = Math.max(0.1, Math.min(3, optimalScale)); // Clamp to our zoom limits

    // Calculate center position with top-left transform origin
    const scaledWidth = svgWidth * finalScale;
    const scaledHeight = svgHeight * finalScale;
    
    // With transform-origin: top left, we need to account for the scaling offset
    // The element scales from top-left, so we need to translate to center it
    const centerX = (availableWidth - scaledWidth) / 2;
    const centerY = (availableHeight - scaledHeight) / 2;

    // Store diagram dimensions for reference
    setDiagramDimensions({ width: svgWidth, height: svgHeight });

    // Apply the calculated zoom and position
    setZoomLevel(finalScale);
    setPanPosition({ x: centerX, y: centerY });
    setIsAutoFitted(true);


  };

  const handleFitToView = () => {
    autoFitAndCenter();
  };

  const handleCenterView = () => {
    if (!ref.current || !containerRef.current) return;

    const svgElement = ref.current.querySelector('svg');
    if (!svgElement) return;

    // Use stored dimensions if available, otherwise detect them
    let svgWidth = diagramDimensions.width;
    let svgHeight = diagramDimensions.height;
    
    if (svgWidth === 0 || svgHeight === 0) {
      const viewBox = svgElement.getAttribute('viewBox');
      if (viewBox) {
        const [, , width, height] = viewBox.split(' ').map(Number);
        svgWidth = width;
        svgHeight = height;
      } else {
        const svgRect = svgElement.getBoundingClientRect();
        svgWidth = svgRect.width;
        svgHeight = svgRect.height;
      }
    }

    const containerRect = containerRef.current.getBoundingClientRect();

    const padding = 32;
    const availableWidth = containerRect.width - padding;
    const availableHeight = containerRect.height - padding;

    const scaledWidth = svgWidth * zoomLevel;
    const scaledHeight = svgHeight * zoomLevel;
    
    // Center the diagram at current zoom level (transform-origin: top left)
    const centerX = (availableWidth - scaledWidth) / 2;
    const centerY = (availableHeight - scaledHeight) / 2;

    setPanPosition({ x: centerX, y: centerY });
  };

  // Image export functions - memoized to prevent unnecessary re-renders
  const downloadSVG = useCallback(() => {
    if (!ref.current) return;

    const svgElement = ref.current.querySelector('svg');
    if (!svgElement) return;

    // Clone SVG to avoid modifying the original
    const svgClone = svgElement.cloneNode(true) as SVGElement;
    
    // Get the actual SVG dimensions (either from viewBox or width/height)
    const viewBox = svgClone.getAttribute('viewBox');
    let width, height;
    
    if (viewBox) {
      const [, , w, h] = viewBox.split(' ').map(Number);
      width = w;
      height = h;
    } else {
      width = svgClone.getAttribute('width') || '800';
      height = svgClone.getAttribute('height') || '600';
    }

    // Ensure the SVG has proper dimensions set
    svgClone.setAttribute('width', width.toString());
    svgClone.setAttribute('height', height.toString());
    svgClone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');

    // Serialize SVG to string
    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(svgClone);
    
    // Create blob and download
    const blob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `mermaid-diagram-${Date.now()}.svg`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, []);

  const downloadPNG = useCallback(async () => {
    if (!ref.current) return;

    const svgElement = ref.current.querySelector('svg');
    if (!svgElement) return;

    try {
      // Clone SVG to avoid modifying the original
      const svgClone = svgElement.cloneNode(true) as SVGElement;
      
      // Get the actual SVG dimensions
      const viewBox = svgClone.getAttribute('viewBox');
      let width, height;
      
      if (viewBox) {
        const [, , w, h] = viewBox.split(' ').map(Number);
        width = w;
        height = h;
      } else {
        width = parseFloat(svgClone.getAttribute('width') || '800');
        height = parseFloat(svgClone.getAttribute('height') || '600');
      }

      // Set a reasonable scale factor for better quality
      const scale = 2; // 2x for crisp images
      const canvasWidth = width * scale;
      const canvasHeight = height * scale;

      // Ensure SVG has proper attributes
      svgClone.setAttribute('width', width.toString());
      svgClone.setAttribute('height', height.toString());
      svgClone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');

      // Convert SVG to data URL
      const serializer = new XMLSerializer();
      const svgString = serializer.serializeToString(svgClone);
      const svgDataUrl = `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(svgString)))}`;

      // Create canvas and draw SVG
      const canvas = document.createElement('canvas');
      canvas.width = canvasWidth;
      canvas.height = canvasHeight;
      const ctx = canvas.getContext('2d');
      
      if (!ctx) {
        throw new Error('Could not get canvas context');
      }

      // Set white background (SVGs are transparent by default)
      ctx.fillStyle = 'white';
      ctx.fillRect(0, 0, canvasWidth, canvasHeight);

      // Create image and draw to canvas
      const img = new window.Image();
      img.onload = () => {
        ctx.drawImage(img, 0, 0, canvasWidth, canvasHeight);
        
        // Convert canvas to PNG and download
        canvas.toBlob((blob) => {
          if (blob) {
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `mermaid-diagram-${Date.now()}.png`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
          }
        }, 'image/png', 0.95); // High quality PNG
      };

      img.onerror = () => {
        console.error('Failed to load SVG for PNG conversion');
        alert('Failed to export PNG. Please try SVG export instead.');
      };

      img.src = svgDataUrl;
    } catch (error) {
      console.error('PNG export error:', error);
      alert('Failed to export PNG. Please try SVG export instead.');
    }
  }, []);

  // Pass download functions to parent component - only call when functions actually change
  useEffect(() => {
    if (onDownloadReady && !renderError) {
      onDownloadReady(downloadSVG, downloadPNG);
    }
  }, [onDownloadReady, downloadSVG, downloadPNG, renderError]);

  const handleWheel = (e: React.WheelEvent) => {
    // Prevent page scrolling but allow diagram zoom
    e.preventDefault();
    e.stopPropagation();
    
    // Calculate zoom delta
    const delta = e.deltaY > 0 ? -0.1 : 0.1;
    setZoomLevel(prev => Math.max(0.1, Math.min(3, prev + delta)));
    setIsAutoFitted(false); // Clear auto-fitted status on manual zoom
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
    setDragStart({ x: e.clientX - panPosition.x, y: e.clientY - panPosition.y });
    setIsAutoFitted(false); // Clear auto-fitted status when user starts panning
  };

  const handleMouseMove = () => {
    // Handled by global listeners for better performance
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleMouseEnter = () => {
    setIsMouseOverDiagram(true);
  };

  const handleMouseLeave = () => {
    setIsMouseOverDiagram(false);
    // Don't stop dragging on mouse leave - let global listeners handle it
  };

  return (
    <div className="w-full">
      {/* Zoom and Pan Controls */}
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
            onClick={handleFitToView}
            variant="outline"
            size="sm"
            className="text-green-600 border-green-300 hover:bg-green-50"
          >
            <Maximize2 className="w-4 h-4 mr-1" />
            Fit to View
          </Button>
          <Button
            onClick={handleCenterView}
            variant="outline"
            size="sm"
            className="text-purple-600 border-purple-300 hover:bg-purple-50"
          >
            <Target className="w-4 h-4 mr-1" />
            Center
          </Button>
          <Button
            onClick={handleResetZoom}
            variant="outline"
            size="sm"
            className="text-gray-600 border-gray-300 hover:bg-gray-50"
          >
            <RotateCcw className="w-4 h-4 mr-1" />
            Reset View
          </Button>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Move className="w-4 h-4" />
          <span>Drag to pan • Scroll to zoom • Fit/Center for optimal view</span>
        </div>
      </div>

      {/* Fixed Diagram Viewport */}
      <div 
        ref={containerRef}
        className="relative w-full bg-white border rounded-lg overflow-hidden select-none"
        style={{ 
          height: '500px', // Fixed height for consistent viewport
          minHeight: '500px',
          maxHeight: '500px',
          // Prevent page scrolling when interacting with diagram
          touchAction: 'none'
        }}
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        {/* Scrollable Inner Container */}
        <div 
          className="absolute inset-0 overflow-hidden"
          style={{
            cursor: isDragging ? 'grabbing' : 'grab',
          }}
        >
          <div 
            ref={ref}
            className="p-4 transition-transform duration-200 ease-out origin-center"
            style={{ 
              transform: `translate(${panPosition.x}px, ${panPosition.y}px) scale(${zoomLevel})`,
              transformOrigin: 'top left',
              minWidth: '100%',
              minHeight: '100%',
              position: 'relative'
            }}
          />
        </div>
        
        {/* Viewport Info Overlay */}
        <div className="absolute top-2 right-2 bg-black bg-opacity-50 text-white text-xs px-2 py-1 rounded max-w-xs">
          <div>Zoom: {Math.round(zoomLevel * 100)}% | Pan: {Math.round(panPosition.x)}, {Math.round(panPosition.y)}</div>
          {diagramDimensions.width > 0 && (
            <div className="text-gray-300">
              Diagram: {Math.round(diagramDimensions.width)} × {Math.round(diagramDimensions.height)}px
            </div>
          )}
          {isAutoFitted && (
            <div className="text-blue-300">🎯 Auto-fitted</div>
          )}
          {isMouseOverDiagram && (
            <div className="text-green-300">🔒 Page scroll locked</div>
          )}
        </div>
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

MermaidDiagram.displayName = 'MermaidDiagram'; 