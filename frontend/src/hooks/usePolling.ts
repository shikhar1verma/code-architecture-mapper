import { useState, useEffect, useCallback, useRef } from 'react';
import { getAnalysisStatus, getAnalysis } from '@/lib/api';
import { AnalysisStatusResponse, AnalysisResult } from '@/types';

interface PollingState {
  status: AnalysisStatusResponse | null;
  result: AnalysisResult | null;
  error: string | null;
  isPolling: boolean;
}

interface UsePollingOptions {
  interval?: number; // Polling interval in milliseconds (default 3000)
  onComplete?: (result: AnalysisResult) => void;
  onError?: (error: string) => void;
}

export function usePolling(analysisId: string | null, options: UsePollingOptions = {}) {
  const { interval = 3000, onComplete, onError } = options;
  
  const [state, setState] = useState<PollingState>({
    status: null,
    result: null,
    error: null,
    isPolling: false,
  });
  
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const isPollingRef = useRef(false);
  
  // Use refs to store callbacks to prevent recreation on every render
  const onCompleteRef = useRef(onComplete);
  const onErrorRef = useRef(onError);
  
  // Update refs when callbacks change
  useEffect(() => {
    onCompleteRef.current = onComplete;
  }, [onComplete]);
  
  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    isPollingRef.current = false;
    setState(prev => ({ ...prev, isPolling: false }));
  }, []);

  const pollStatus = useCallback(async (id: string) => {
    try {
      const statusResponse = await getAnalysisStatus(id);
      
      setState(prev => ({ ...prev, status: statusResponse, error: null }));
      
      // Check if analysis is completed or failed
      if (statusResponse.status === 'completed' || statusResponse.status === 'complete') {
        // Clear polling
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
        isPollingRef.current = false;
        setState(prev => ({ ...prev, isPolling: false }));
        
        // Fetch full analysis results
        try {
          const result = await getAnalysis(id);
          setState(prev => ({ ...prev, result, error: null }));
          onCompleteRef.current?.(result);
        } catch (err) {
          const errorMessage = err instanceof Error ? err.message : 'Failed to retrieve analysis results';
          setState(prev => ({ ...prev, error: errorMessage }));
          onErrorRef.current?.(errorMessage);
        }
      } else if (statusResponse.status === 'failed') {
        // Clear polling
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
        isPollingRef.current = false;
        setState(prev => ({ ...prev, isPolling: false }));
        
        const errorMessage = statusResponse.message || 'Analysis failed';
        setState(prev => ({ ...prev, error: errorMessage }));
        onErrorRef.current?.(errorMessage);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get analysis status';
      setState(prev => ({ ...prev, error: errorMessage }));
      
      // Clear polling on error
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      isPollingRef.current = false;
      setState(prev => ({ ...prev, isPolling: false }));
      
      onErrorRef.current?.(errorMessage);
    }
  }, []);

  const startPolling = useCallback((id: string) => {
    if (isPollingRef.current || !id) return;
    
    isPollingRef.current = true;
    setState(prev => ({ ...prev, isPolling: true, error: null }));
    
    // Initial poll
    pollStatus(id);
    
    // Set up interval polling
    intervalRef.current = setInterval(() => {
      if (isPollingRef.current) {
        pollStatus(id);
      }
    }, interval);
  }, [interval, pollStatus]);

  useEffect(() => {
    if (analysisId && !isPollingRef.current) {
      startPolling(analysisId);
    }
    
    return () => {
      stopPolling();
    };
  }, [analysisId, startPolling, stopPolling]);

  return {
    ...state,
    startPolling,
    stopPolling,
  };
}
