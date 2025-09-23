import { AnalysisRequest, AnalysisResponse, AnalysisResult, DiagramGenerationResponse, ExampleSummary, ExampleData, RefreshAnalysisRequest, AnalysisStatusResponse } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export async function startAnalysis(request: AnalysisRequest): Promise<AnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/analysis/start`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    console.log('Response not ok:', response.status, response.statusText);
    
    // Special handling for quota exhaustion (429)
    if (response.status === 429) {
      try {
        const errorData = await response.json();
        console.log('429 error data:', errorData);
        throw new Error('quota_exhausted');
      } catch {
        console.log('Could not parse 429 response, using fallback');
        throw new Error('quota_exhausted');
      }
    }
    
    // Try to get the detailed error message from the response for other errors
    try {
      const errorData = await response.json();
      console.log('Error data:', errorData);
      const errorDetail = errorData.detail || response.statusText;
      throw new Error(errorDetail);
    } catch {
      // If we can't parse the response, fall back to status text
      throw new Error(`Analysis failed: ${response.statusText}`);
    }
  }

  return response.json();
}

export async function refreshAnalysis(request: RefreshAnalysisRequest): Promise<AnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/analysis/refresh`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    console.log('Refresh response not ok:', response.status, response.statusText);
    
    // Special handling for quota exhaustion (429)
    if (response.status === 429) {
      try {
        const errorData = await response.json();
        console.log('429 error data:', errorData);
        throw new Error('quota_exhausted');
      } catch {
        console.log('Could not parse 429 response, using fallback');
        throw new Error('quota_exhausted');
      }
    }
    
    // Try to get the detailed error message from the response for other errors
    try {
      const errorData = await response.json();
      console.log('Refresh error data:', errorData);
      const errorDetail = errorData.detail || response.statusText;
      throw new Error(errorDetail);
    } catch {
      // If we can't parse the response, fall back to status text
      throw new Error(`Analysis refresh failed: ${response.statusText}`);
    }
  }

  return response.json();
}

export async function getAnalysisStatus(analysisId: string): Promise<AnalysisStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/analysis/${analysisId}/status`);

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Analysis not found');
    }
    throw new Error(`Failed to get analysis status: ${response.statusText}`);
  }

  return response.json();
}

export async function getAnalysis(analysisId: string): Promise<AnalysisResult> {
  const response = await fetch(`${API_BASE_URL}/analysis/${analysisId}`);

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Analysis not found');
    }
    if (response.status === 425) {
      // Too Early - analysis not yet completed
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Analysis not yet completed');
    }
    throw new Error(`Failed to get analysis: ${response.statusText}`);
  }

  return response.json();
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function getExamples(): Promise<any[]> {
  const response = await fetch(`${API_BASE_URL}/examples`);

  if (!response.ok) {
    throw new Error(`Failed to get examples: ${response.statusText}`);
  }

  return response.json();
}

export async function generateDiagramOnDemand(analysisId: string, mode: string): Promise<DiagramGenerationResponse> {
  const response = await fetch(`${API_BASE_URL}/analysis/${analysisId}/diagram/${mode}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to generate diagram: ${response.statusText}`);
  }

  return response.json();
}

export interface MermaidRetryRequest {
  broken_mermaid_code: string;
  error_message: string;
}

export interface MermaidRetryResponse {
  mode: string;
  original_diagram: string;
  corrected_diagram: string;
  status: string;
}

export async function retryMermaidDiagram(
  analysisId: string, 
  mode: string, 
  request: MermaidRetryRequest
): Promise<MermaidRetryResponse> {
  console.log(`🔄 Retrying Mermaid diagram - Mode: ${mode}, Error: ${request.error_message.substring(0, 100)}${request.error_message.length > 100 ? '...' : ''}`);
  
  const response = await fetch(`${API_BASE_URL}/analysis/${analysisId}/diagram/${mode}/retry`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    console.error(`❌ Retry failed with status: ${response.status}`);
    
    // Special handling for quota exhaustion (429)
    if (response.status === 429) {
      throw new Error('quota_exhausted');
    }
    
    try {
      const errorData = await response.json();
      console.error('Retry error details:', errorData);
      const errorDetail = errorData.detail || response.statusText;
      throw new Error(errorDetail);
    } catch {
      throw new Error(`Failed to retry diagram: ${response.statusText}`);
    }
  }

  const result = await response.json();
  console.log(`✅ Retry successful - Mode: ${mode}, New diagram length: ${result.corrected_diagram?.length || 0}`);
  return result;
}

// Example API functions
export async function fetchExamples(): Promise<ExampleSummary[]> {
  const response = await fetch(`${API_BASE_URL}/examples/`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    console.error('❌ Failed to fetch examples:', response.statusText);
    throw new Error(`Failed to fetch examples: ${response.statusText}`);
  }

  const examples = await response.json();
  console.log(`✅ Retrieved ${examples.length} examples`);
  return examples;
}

export async function fetchExampleData(exampleId: string): Promise<ExampleData> {
  const response = await fetch(`${API_BASE_URL}/examples/${exampleId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Example not found');
    }
    console.error('❌ Failed to fetch example data:', response.statusText);
    throw new Error(`Failed to fetch example data: ${response.statusText}`);
  }

  const exampleData = await response.json();
  return exampleData;
} 