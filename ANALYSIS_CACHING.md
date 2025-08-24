# Analysis Caching Feature

## Overview

The Code Architecture Mapper now includes intelligent caching functionality to improve performance and reduce redundant analysis requests. This feature automatically detects when a repository has been previously analyzed and provides options to use cached results or refresh with latest data.

## How It Works

### Backend Caching Logic

1. **Check for Existing Analysis**: When a new analysis request is submitted, the system first checks if an analysis already exists for the given repository URL
2. **Return Cached Results**: If found and the analysis is complete, it returns the existing analysis ID with `cached: true`
3. **Fresh Analysis**: If no previous analysis exists or `force_refresh` is requested, a new analysis is performed

### Frontend User Experience

1. **Cached Results Display**: When cached results are shown, users see:
   - "Analysis Retrieved from Cache" message
   - Date when the analysis was originally performed
   - A "Refresh" button to get latest analysis

2. **Refresh Functionality**: Users can click the refresh button to:
   - Re-analyze the repository with latest data
   - Update the existing analysis record (preserves analysis ID)
   - Get fresh insights from current repository state

## API Endpoints

### POST `/api/analyze`
- **Purpose**: Start new analysis or return cached results
- **Request**: `{ "repo_url": "string", "force_refresh": false }`
- **Response**: `{ "analysis_id": "string", "status": "complete", "cached": boolean, "cached_at": "string" }`

### POST `/api/analyze/refresh`
- **Purpose**: Refresh existing analysis with latest data
- **Request**: `{ "analysis_id": "string" }`
- **Response**: `{ "analysis_id": "string", "status": "complete", "cached": false }`

## Benefits

1. **Performance**: Instant results for previously analyzed repositories
2. **Cost Efficiency**: Reduces LLM API calls for repeated analyses
3. **User Experience**: Clear indication of cached vs fresh results
4. **Flexibility**: Easy refresh option when latest analysis is needed

## Technical Implementation

- **Database**: Uses existing `Analysis` table with URL-based lookup
- **Caching Strategy**: Most recent analysis per repository URL
- **Update Logic**: Refresh updates existing record instead of creating new one
- **Frontend State**: Tracks cached status and provides appropriate UI feedback

## Usage Examples

### First Analysis
```
User submits: https://github.com/user/repo
→ New analysis performed
→ Shows: "Analysis Complete"
```

### Subsequent Analysis
```
User submits: https://github.com/user/repo (same URL)
→ Cached results returned
→ Shows: "Analysis Retrieved from Cache (analyzed on MM/DD/YYYY)"
→ Refresh button available
```

### Refresh Analysis
```
User clicks "Refresh" button
→ Fresh analysis performed
→ Existing record updated
→ Shows: "Analysis Complete"
``` 