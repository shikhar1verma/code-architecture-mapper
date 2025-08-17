'use client';

import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

interface MermaidDiagramProps {
  chart: string;
  id?: string;
}

export function MermaidDiagram({ chart, id = 'mermaid-diagram' }: MermaidDiagramProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current || !chart) return;

    mermaid.initialize({
      startOnLoad: true,
      theme: 'default',
      securityLevel: 'loose',
    });

    const uniqueId = `${id}-${Date.now()}`;
    
    const renderDiagram = async () => {
      try {
        const { svg } = await mermaid.render(uniqueId, chart);
        if (ref.current) {
          ref.current.innerHTML = svg;
        }
      } catch (error) {
        console.error('Mermaid rendering error:', error);
        if (ref.current) {
          ref.current.innerHTML = `<div class="text-red-500 p-4 bg-red-50 rounded">
            Error rendering diagram: ${error instanceof Error ? error.message : 'Unknown error'}
          </div>`;
        }
      }
    };

    renderDiagram();
  }, [chart, id]);

  return (
    <div 
      ref={ref}
      className="w-full overflow-auto bg-white border rounded-lg p-4"
      style={{ minHeight: '200px' }}
    />
  );
} 