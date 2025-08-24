# Gemini API Retry Mechanism with Fallback Models

## Overview

This system implements an intelligent retry mechanism with fallback models for the Gemini API to maximize availability and handle quota limitations gracefully.

## How It Works

### Model Fallback Order

The system tries models in this order (from best quality to highest availability):

1. **gemini-2.5-flash** - Best model (10 RPM, 250K TPM, 250 RPD)
2. **gemini-2.5-flash-lite** - Good model (15 RPM, 250K TPM, 1000 RPD)  
3. **gemini-2.0-flash** - Good model (15 RPM, 1M TPM, 200 RPD)
4. **gemini-2.0-flash-lite** - Fastest model (30 RPM, 1M TPM, 200 RPD)
5. **Legacy fallback** - Configured via `GEMINI_MODEL` env var (default: gemini-1.5-flash)

### Retry Logic

For each model, the system:
- Tries the model up to `MAX_RETRIES_PER_MODEL` times (default: 2)
- Waits 2-5 seconds (random) between retries
- On quota exhaustion (429 error), immediately moves to next model
- On service errors (500/503), retries the same model before moving on
- Only raises `GeminiQuotaExhaustedError` when ALL models fail

## Configuration

### Environment Variables

```bash
# Legacy model configuration (still used as final fallback)
GEMINI_MODEL=gemini-1.5-flash

# Retry timing
RETRY_MIN_DELAY_SECONDS=2
RETRY_MAX_DELAY_SECONDS=5
MAX_RETRIES_PER_MODEL=2
```

### Config Variables

In `backend/config.py`:

```python
# Model order (highest quality to highest availability)
GEMINI_MODEL_FALLBACK_ORDER = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite", 
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    GEMINI_MODEL,  # Legacy fallback
]

# Retry configuration
RETRY_MIN_DELAY_SECONDS = 2
RETRY_MAX_DELAY_SECONDS = 5
MAX_RETRIES_PER_MODEL = 2
```

## Usage

The retry mechanism is transparent to existing code:

```python
from backend.llm.gemini import generate_markdown, generate_json, GeminiQuotaExhaustedError

# Markdown generation with automatic fallback
try:
    result = generate_markdown(system_prompt, user_prompt)
except GeminiQuotaExhaustedError:
    # Only raised when ALL models are exhausted
    print("All models exhausted - try again later")

# JSON generation with automatic fallback  
try:
    result = generate_json(system_prompt, user_prompt, ResponseSchema)
except GeminiQuotaExhaustedError:
    print("All models exhausted - try again later")
```

## Log Output

The system provides detailed logging:

```
🤖 Trying model: gemini-2.5-flash
🚫 Model gemini-2.5-flash quota exhausted (attempt 1)
🤖 Trying model: gemini-2.5-flash-lite
⏳ Waiting 3.2s before retry...
🔄 Retry 2/2 for gemini-2.5-flash-lite
✅ Success with gemini-2.5-flash-lite
```

## Error Handling

### GeminiQuotaExhaustedError
- Raised only when ALL fallback models are exhausted
- Contains list of attempted models
- Indicates system-wide quota exhaustion

### GeminiAPIError
- Raised for unexpected API errors
- Includes original error details
- Does not trigger fallback (non-quota errors)

## Benefits

1. **Maximum Uptime**: Uses multiple models to avoid service interruption
2. **Optimal Quality**: Always tries best available model first  
3. **Quota Efficiency**: Distributes load across different model quotas
4. **Transparent**: No code changes needed for existing implementations
5. **Detailed Logging**: Clear visibility into which models are working

## Testing

Run the test script to verify functionality:

```bash
python test_retry_mechanism.py
```

This will test:
- Configuration loading
- Markdown generation with fallback
- JSON generation with fallback

## Model Quota Information

| Model | RPM | TPM (input) | RPD | Notes |
|-------|-----|-------------|-----|-------|
| 2.5 Flash | 10 | 250,000 | 250 | Highest quality |
| 2.5 Flash-Lite | 15 | 250,000 | 1,000 | Good balance |
| 2.0 Flash | 15 | 1,000,000 | 200 | High TPM |
| 2.0 Flash-Lite | 30 | 1,000,000 | 200 | Highest RPM |

## Future Enhancements

- Dynamic model ordering based on current quota status
- Per-model success rate tracking
- Intelligent backoff based on quota reset times
- Circuit breaker pattern for consistently failing models 