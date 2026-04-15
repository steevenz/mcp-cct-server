# Guide: CCT MCP Server Configuration

This guide provides detailed explanations for all configuration options available in the CCT MCP Server. Configuration is managed through the `.env` file in the project root.

## Table of Contents
1. [Getting Started](#1-getting-started)
2. [Server Settings](#2-server-settings)
3. [Logging Configuration](#3-logging-configuration)
4. [Database & Storage](#4-database--storage)
5. [AI Model Configuration](#5-ai-model-configuration)
6. [User Operational Preferences](#6-user-operational-preferences)
7. [Forex / Currency Conversion](#7-forex--currency-conversion)
8. [LLM Provider Configuration](#8-llm-provider-configuration)
9. [Advanced Configuration](#9-advanced-configuration)
10. [Configuration Examples](#10-configuration-examples)

---

## 1. Getting Started

### Creating Your Configuration File

The first step is to copy the example configuration file:

```bash
cp .env.example .env
```

This creates your local `.env` file that the server will use. Never commit `.env` to version control as it may contain sensitive API keys.

### Configuration Priority

The server reads configuration in this priority order:
1. Environment variables set in the system
2. Values in `.env` file
3. Default values hardcoded in the application

---

## 2. Server Settings

### CCT_SERVER_NAME

**Description:** Server name identifier used in MCP handshake and logging

**Default:** `cct-mcp-server`

**Example:**
```env
CCT_SERVER_NAME=production-cct-server
```

**Use Cases:**
- Distinguishing between multiple CCT instances
- Identifying servers in logs and monitoring
- Custom naming for different environments (dev, staging, production)

---

### CCT_TRANSPORT

**Description:** Transport mode for MCP communication

**Options:**
- `stdio` - Standard input/output (default, best for IDE integration)
- `http` - HTTP server (alias for SSE)
- `sse` - Server-Sent Events (for multi-agent setups)
- `streamable-http` - Streaming HTTP (experimental)

**Default:** `stdio`

**Examples:**
```env
# Single IDE integration (recommended)
CCT_TRANSPORT=stdio

# Multi-agent / multi-IDE setup
CCT_TRANSPORT=sse

# Background service
CCT_TRANSPORT=sse
```

**When to Use Each:**
- **stdio**: Direct IDE integration, single connection, lowest latency
- **sse**: Multiple IDEs/agents, background services, HTTP clients
- **streamable-http**: Experimental streaming HTTP support

**Important Notes:**
- Windows Service **must** use SSE mode (stdio not supported in services)
- Multi-agent setups require SSE mode
- Changing transport mode requires server restart

---

### CCT_HOST

**Description:** Host address for HTTP/SSE transport

**Options:**
- `0.0.0.0` - Bind to all network interfaces (default)
- `127.0.0.1` - Localhost only (more secure)
- `localhost` - Localhost only
- Specific IP address (e.g., `192.168.1.100`)

**Default:** `0.0.0.0`

**Examples:**
```env
# Accept connections from any interface (multi-IDE)
CCT_HOST=0.0.0.0

# Local development only (more secure)
CCT_HOST=127.0.0.1

# Specific network interface
CCT_HOST=192.168.1.100
```

**Security Considerations:**
- `0.0.0.0` allows connections from any machine on the network
- `127.0.0.1` only allows local connections
- Use `127.0.0.1` for single-machine setups
- Use `0.0.0.0` only when multi-machine access is needed

**Ignored in stdio mode** - This setting only applies to SSE/HTTP transport.

---

### CCT_PORT

**Description:** Port number for HTTP/SSE transport

**Range:** `1-65535`

**Default:** `8000`

**Examples:**
```env
# Default port
CCT_PORT=8000

# Custom port (avoid conflicts)
CCT_PORT=8001

# Standard HTTP port (requires admin)
CCT_PORT=80
```

**Port Selection Guidelines:**
- Use ports `8000-8999` for application servers
- Avoid well-known ports (below 1024) unless necessary
- Ensure firewall allows traffic on chosen port
- Check for port conflicts before starting

**Ignored in stdio mode** - This setting only applies to SSE/HTTP transport.

---

### CCT_MAX_SESSIONS

**Description:** Maximum number of concurrent sessions/connections

**Range:** `1-100000`

**Default:** `128`

**Examples:**
```env
# Development / personal use
CCT_MAX_SESSIONS=10

# Small team
CCT_MAX_SESSIONS=50

# Large organization
CCT_MAX_SESSIONS=500

# Maximum capacity
CCT_MAX_SESSIONS=100000
```

**Performance Impact:**
- Higher values allow more concurrent users
- Each session consumes memory and CPU
- Monitor server resources when increasing
- Start low and increase based on demand

**Use Cases:**
- Single developer: `10-50`
- Small team: `50-100`
- Large organization: `100-500`
- Public service: `500+`

---

## 3. Logging Configuration

### CCT_LOG_LEVEL

**Description:** Logging verbosity level

**Options:**
- `DEBUG` - Detailed diagnostic information (development)
- `INFO` - General informational messages (default)
- `WARNING` - Warning messages (production)
- `ERROR` - Error messages only (minimal)
- `CRITICAL` - Critical errors only (emergency)

**Default:** `INFO`

**Examples:**
```env
# Development - see everything
CCT_LOG_LEVEL=DEBUG

# Production - normal operation
CCT_LOG_LEVEL=INFO

# Production - reduce noise
CCT_LOG_LEVEL=WARNING

# Minimal logging
CCT_LOG_LEVEL=ERROR
```

**When to Use Each:**
- **DEBUG**: Development, troubleshooting, debugging
- **INFO**: Normal operation, monitoring
- **WARNING**: Production with reduced noise
- **ERROR**: Production when only errors matter
- **CRITICAL**: Emergency situations only

**Performance Impact:**
- DEBUG logging can impact performance due to verbosity
- WARNING and ERROR levels have minimal performance impact
- Consider using WARNING for high-traffic production servers

---

## 4. Database & Storage

### CCT_DB_PATH

**Description:** Path to SQLite database file for session persistence

**Format:** Relative to project root or absolute path

**Default:** `database/cct_memory.db`

**Examples:**
```env
# Default location
CCT_DB_PATH=database/cct_memory.db

# Custom relative path
CCT_DB_PATH=data/cct_memory.db

# Absolute path (Windows)
CCT_DB_PATH=C:/data/cct/cct_memory.db

# Absolute path (Linux/macOS)
CCT_DB_PATH=/var/lib/cct/cct_memory.db
```

**Database Contents:**
- Session history
- Thought patterns
- Memory cache
- User preferences
- Learning data

**Backup Recommendations:**
- Regular backups of the database file
- Store backups in a separate location
- Consider using absolute paths for consistent backup locations
- Database grows over time - monitor disk space

**Migration:**
- Database location can be changed by updating this variable
- Existing data can be copied to new location
- Server restart required for changes to take effect

---

### CCT_PRICING_PATH

**Description:** Path to directory containing model pricing JSON files

**Format:** Relative to project root or absolute path

**Default:** `database/datasets`

**Examples:**
```env
# Default location
CCT_PRICING_PATH=database/datasets

# Custom relative path
CCT_PRICING_PATH=data/pricing

# Absolute path (Windows)
CCT_PRICING_PATH=C:/data/cct/pricing

# Absolute path (Linux/macOS)
CCT_PRICING_PATH=/var/lib/cct/pricing
```

**Pricing File Format:**
Each model requires a JSON file with pricing information:
```json
{
  "model_id": "claude-3-5-sonnet-20240620",
  "name": "Claude 3.5 Sonnet",
  "provider": "anthropic",
  "input_price_per_1k": 0.003,
  "output_price_per_1k": 0.015,
  "max_tokens": 200000
}
```

**Custom Models:**
- Add new model pricing files to this directory
- Model ID must match filename (or be specified in file)
- Used for cost calculation and model selection
- Server restart required for new models to be recognized

---

## 5. AI Model Configuration

### CCT_DEFAULT_MODEL

**Description:** Default AI model for cognitive processing

**Format:** Model ID matching pricing directory

**Default:** `claude-3-5-sonnet-20240620`

**Examples:**
```env
# Claude 3.5 Sonnet (balanced)
CCT_DEFAULT_MODEL=claude-3-5-sonnet-20240620

# GPT-4o (fast, cost-effective)
CCT_DEFAULT_MODEL=gpt-4o

# Claude 3 Opus (highest quality)
CCT_DEFAULT_MODEL=claude-3-opus-20240229

# Custom model
CCT_DEFAULT_MODEL=my-custom-model
```

**Model Selection Criteria:**
- **Speed**: GPT-4o, Gemini 1.5 Flash
- **Quality**: Claude 3 Opus, Claude 3.5 Sonnet
- **Cost**: GPT-4o, Gemini 1.5 Flash
- **Context**: Claude 3.5 Sonnet (200K tokens)

**Requirements:**
- Model ID must exist in pricing directory
- API key for corresponding provider must be configured
- Model must be available in your region

**Changing Models:**
- Update this variable in `.env`
- Restart server for changes to take effect
- Consider testing new models before switching default

---

## 6. User Operational Preferences

### CCT_MAX_THOUGHTS

**Description:** Maximum number of thoughts per cognitive session

**Range:** `10-10000`

**Default:** `200`

**Examples:**
```env
# Quick tasks (minimal depth)
CCT_MAX_THOUGHTS=50

# Balanced depth (default)
CCT_MAX_THOUGHTS=200

# Deep analysis
CCT_MAX_THOUGHTS=500

# Maximum depth
CCT_MAX_THOUGHTS=10000
```

**Impact:**
- **Lower values**: Faster processing, less detailed analysis
- **Higher values**: Deeper analysis, more comprehensive reasoning
- **Trade-off**: Speed vs. depth of reasoning

**Use Cases:**
- Quick code review: `50-100`
- Standard analysis: `200-500`
- Deep research: `500-1000`
- Maximum depth: `1000+`

**Performance Impact:**
- Each thought consumes LLM tokens
- Higher values increase cost and processing time
- Monitor token usage when increasing

---

### CCT_MAX_CONTENT_LENGTH

**Description:** Maximum content length per thought in characters

**Range:** `100-100000`

**Default:** `8000`

**Examples:**
```env
# Concise thoughts
CCT_MAX_CONTENT_LENGTH=2000

# Balanced length (default)
CCT_MAX_CONTENT_LENGTH=8000

# Detailed thoughts
CCT_MAX_CONTENT_LENGTH=20000

# Maximum detail
CCT_MAX_CONTENT_LENGTH=100000
```

**Impact:**
- **Lower values**: Faster processing, less detailed thoughts
- **Higher values**: More detailed thoughts, better context
- **Trade-off**: Speed vs. detail level

**Use Cases:**
- Quick summaries: `2000-4000`
- Standard analysis: `8000-12000`
- Detailed documentation: `15000-20000`

**Token Impact:**
- Directly affects token usage per thought
- Longer thoughts may exceed context limits
- Consider context window when setting

---

### CCT_MAX_CONTEXT_TOKENS

**Description:** Maximum context tokens sent to LLM per request

**Range:** `1000-128000`

**Default:** `4000`

**Examples:**
```env
# Minimal context (fast, cheap)
CCT_MAX_CONTEXT_TOKENS=2000

# Balanced context (default)
CCT_MAX_CONTEXT_TOKENS=4000

# Large context (better understanding)
CCT_MAX_CONTEXT_TOKENS=16000

# Maximum context (Claude 3.5)
CCT_MAX_CONTEXT_TOKENS=200000
```

**Impact:**
- **Lower values**: Faster, cheaper, less context
- **Higher values**: Better understanding, more expensive
- **Trade-off**: Cost vs. comprehension

**Model-Specific Limits:**
- GPT-4o: 128K tokens
- Claude 3.5 Sonnet: 200K tokens
- Gemini 1.5: 1M tokens
- Ensure value doesn't exceed model's context window

**Use Cases:**
- Simple tasks: `2000-4000`
- Complex analysis: `8000-16000`
- Long-context tasks: `32000+`

---

### CCT_CONTEXT_STRATEGY

**Description:** Strategy for managing context when approaching limits

**Options:**
- `full` - Keep full context until limit (may truncate)
- `sliding` - Sliding window (keep most recent)
- `summarized` - Summarize older context (default)
- `branch_only` - Keep only current thought branch

**Default:** `summarized`

**Examples:**
```env
# Keep full context (may truncate at limit)
CCT_CONTEXT_STRATEGY=full

# Sliding window (most recent)
CCT_CONTEXT_STRATEGY=sliding

# Summarize older context (default)
CCT_CONTEXT_STRATEGY=summarized

# Current branch only
CCT_CONTEXT_STRATEGY=branch_only
```

**Strategy Explanations:**

**full**: 
- Keeps all context until limit reached
- May truncate abruptly at limit
- Best for short sessions

**sliding**: 
- Keeps most recent N tokens
- Older context is discarded
- Good for continuous processing

**summarized**: 
- Summarizes older context
- Preserves key information
- Balances detail and context
- **Recommended for most use cases**

**branch_only**: 
- Keeps only current thought branch
- Discards parallel branches
- Best for focused tasks

**Selection Guidelines:**
- Short sessions: `full` or `sliding`
- Long sessions: `summarized`
- Focused tasks: `branch_only`
- General purpose: `summarized`

---

### CCT_TP_THRESHOLD

**Description:** Golden Thinking Pattern quality threshold (0.0-1.0)

**Range:** `0.0-1.0`

**Default:** `0.9`

**Examples:**
```env
# Very permissive (accept most patterns)
CCT_TP_THRESHOLD=0.7

# Balanced (default)
CCT_TP_THRESHOLD=0.9

# Very strict (only high-quality patterns)
CCT_TP_THRESHOLD=0.95

# Maximum strictness
CCT_TP_THRESHOLD=1.0
```

**Impact:**
- **Lower values**: More patterns accepted, less quality control
- **Higher values**: Stricter quality, fewer patterns accepted
- **Trade-off**: Quantity vs. quality of patterns

**Use Cases:**
- Exploratory analysis: `0.7-0.8`
- Standard operation: `0.9`
- High-quality output: `0.95`
- Maximum quality: `1.0`

**Golden Thinking Patterns:**
- High-quality reasoning patterns
- Learned from successful sessions
- Used for pattern matching and learning
- Higher threshold = better pattern quality

---

## 7. Forex / Currency Conversion

### CCT_FOREX_CACHE_TTL

**Description:** Time-to-live for forex exchange rate cache in seconds

**Range:** `60-604800` (1 minute to 7 days)

**Default:** `86400` (24 hours)

**Examples:**
```env
# Frequent updates (1 hour)
CCT_FOREX_CACHE_TTL=3600

# Daily updates (default)
CCT_FOREX_CACHE_TTL=86400

# Weekly updates
CCT_FOREX_CACHE_TTL=604800
```

**Impact:**
- **Lower values**: More accurate rates, more API calls
- **Higher values**: Less accurate rates, fewer API calls
- **Trade-off**: Accuracy vs. API usage

**Use Cases:**
- Real-time trading: `60-300` (1-5 minutes)
- Daily operations: `86400` (24 hours)
- Historical analysis: `604800` (7 days)

**API Considerations:**
- Some forex APIs have rate limits
- Cache helps avoid rate limit issues
- Default API (Frankfurter) is free and unlimited

---

### CCT_FOREX_DEFAULT_RATE

**Description:** Fallback USD to IDR exchange rate if API fails

**Range:** `1000-50000`

**Default:** `17095.0` (April 2026 baseline)

**Examples:**
```env
# Conservative estimate
CCT_FOREX_DEFAULT_RATE=15000.0

# Current baseline (default)
CCT_FOREX_DEFAULT_RATE=17095.0

# Optimistic estimate
CCT_FOREX_DEFAULT_RATE=18000.0
```

**Purpose:**
- Fallback when forex API is unavailable
- Ensures currency conversion always works
- Should be updated periodically for accuracy

**Updating:**
- Check current USD to IDR rate
- Update this value monthly or quarterly
- Use a conservative estimate to avoid overestimation

**Currency Pairs:**
- Currently supports USD to IDR
- Can be extended for other pairs
- Used in cost calculations and reporting

---

### CCT_FOREX_API_URL

**Description:** API endpoint for live forex exchange rates

**Default:** `https://api.frankfurter.app/latest?from=USD&to=IDR`

**Examples:**
```env
# Default (Frankfurter - free, no API key)
CCT_FOREX_API_URL=https://api.frankfurter.app/latest?from=USD&to=IDR

# Custom API endpoint
CCT_FOREX_API_URL=https://api.exchangerate-api.com/v4/latest/USD
```

**API Requirements:**
- Must return JSON with exchange rate data
- Should support HTTPS
- May require API key (add to URL if needed)

**Alternative APIs:**
- Frankfurter (free, no key required)
- ExchangeRate-API (free tier available)
- Open Exchange Rates (API key required)

**Custom Integration:**
- Can integrate with any forex API
- Ensure response format is compatible
- Test API endpoint before using in production

---

## 8. LLM Provider Configuration

### CCT_LLM_PROVIDER

**Description:** Primary LLM provider for cognitive processing

**Options:**
- `gemini` - Google Gemini (default)
- `openai` - OpenAI GPT models
- `anthropic` - Anthropic Claude models
- `ollama` - Local Ollama models
- `deepseek` - DeepSeek models
- `groq` - Groq (fast inference)
- `mistral` - Mistral AI models

**Default:** `gemini`

**Examples:**
```env
# Google Gemini (default)
CCT_LLM_PROVIDER=gemini

# OpenAI
CCT_LLM_PROVIDER=openai

# Anthropic Claude
CCT_LLM_PROVIDER=anthropic

# Local Ollama
CCT_LLM_PROVIDER=ollama

# Groq (fast inference)
CCT_LLM_PROVIDER=groq
```

**Provider Comparison:**

| Provider | Speed | Quality | Cost | Notes |
|----------|-------|---------|------|-------|
| gemini | Fast | High | Low | Best value |
| openai | Fast | High | Medium | GPT-4o |
| anthropic | Medium | Very High | High | Best quality |
| ollama | Variable | Variable | Free | Local only |
| groq | Very Fast | High | Low | Fastest inference |
| mistral | Fast | High | Low | Good value |

**Selection Guidelines:**
- **Best overall**: Gemini (speed, quality, cost)
- **Best quality**: Anthropic Claude
- **Fastest**: Groq
- **Local/Offline**: Ollama
- **Enterprise**: OpenAI

**Guided Mode:**
- Leave empty for **Guided Mode** (no LLM)
- Provides structured instructions instead of autonomous reasoning
- Useful when API keys are not available

---

### API Keys

**Description:** API keys for various LLM providers

**Format:** Provider-specific API keys

**Examples:**
```env
# Google Gemini
GEMINI_API_KEY=your_gemini_api_key_here

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic Claude
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# DeepSeek
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Groq
GROQ_API_KEY=your_groq_api_key_here

# Mistral
MISTRAL_API_KEY=your_mistral_api_key_here
```

**Getting API Keys:**

**Google Gemini:**
1. Visit [Google AI Studio](https://aistudio.google.com/)
2. Create API key
3. Copy to `.env`

**OpenAI:**
1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Create API key
3. Copy to `.env`

**Anthropic:**
1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Create API key
3. Copy to `.env`

**Security Best Practices:**
- Never commit `.env` to version control
- Rotate API keys periodically
- Use environment-specific keys (dev/staging/prod)
- Monitor API key usage and costs

**Multiple Providers:**
- Configure all providers you might use
- Server will use the one specified in `CCT_LLM_PROVIDER`
- Useful for testing different providers
- Allows easy switching between providers

---

### OLLAMA_BASE_URL

**Description:** Base URL for local Ollama instance

**Default:** `http://localhost:11434`

**Examples:**
```env
# Default (local)
OLLAMA_BASE_URL=http://localhost:11434

# Remote Ollama instance
OLLAMA_BASE_URL=http://192.168.1.100:11434

# Custom port
OLLAMA_BASE_URL=http://localhost:11435
```

**Ollama Setup:**
1. Install Ollama: https://ollama.ai/
2. Start Ollama service: `ollama serve`
3. Pull models: `ollama pull llama2`, `ollama pull mistral`
4. Configure base URL in `.env`

**Use Cases:**
- Local development without API keys
- Privacy-sensitive applications
- Offline operation
- Custom fine-tuned models

**Network Configuration:**
- Ensure Ollama is accessible from CCT server
- May require firewall configuration for remote access
- Use `127.0.0.1` for local-only access
- Use `0.0.0.0` for network access

---

## 9. Advanced Configuration

### Custom Database Location

For production deployments, consider using absolute paths:

```env
CCT_DB_PATH=/var/lib/cct/cct_memory.db
CCT_PRICING_PATH=/etc/cct/pricing
```

**Benefits:**
- Consistent location across deployments
- Easier backup and monitoring
- Better separation from application code

---

### Environment-Specific Configuration

Create different `.env` files for different environments:

```bash
# Development
cp .env.example .env.development

# Staging
cp .env.example .env.staging

# Production
cp .env.example .env.production
```

Then load the appropriate environment:

```bash
# Linux/macOS
export $(cat .env.production | xargs)

# Windows PowerShell
Get-Content .env.production | ForEach-Object {
    $var = $_.Split('=')
    [Environment]::SetEnvironmentVariable($var[0], $var[1])
}
```

---

### Performance Tuning

For high-performance deployments:

```env
# Reduce logging overhead
CCT_LOG_LEVEL=WARNING

# Increase session capacity
CCT_MAX_SESSIONS=500

# Optimize context management
CCT_CONTEXT_STRATEGY=sliding
CCT_MAX_CONTEXT_TOKENS=8000

# Balance quality and speed
CCT_TP_THRESHOLD=0.85
CCT_MAX_THOUGHTS=150
```

---

### Cost Optimization

To minimize LLM API costs:

```env
# Use cost-effective provider
CCT_LLM_PROVIDER=gemini

# Reduce context usage
CCT_MAX_CONTEXT_TOKENS=2000
CCT_MAX_CONTENT_LENGTH=4000

# Limit thought depth
CCT_MAX_THOUGHTS=100

# Use sliding context strategy
CCT_CONTEXT_STRATEGY=sliding
```

---

### Security Hardening

For production security:

```env
# Restrict network access
CCT_HOST=127.0.0.1

# Reduce logging verbosity
CCT_LOG_LEVEL=WARNING

# Use secure database location
CCT_DB_PATH=/var/lib/cct/cct_memory.db

# Rotate API keys regularly
# (manual process)
```

---

## 10. Configuration Examples

### Development Setup

```env
# Server Settings
CCT_SERVER_NAME=dev-cct-server
CCT_TRANSPORT=stdio
CCT_HOST=127.0.0.1
CCT_PORT=8000
CCT_MAX_SESSIONS=10

# Logging
CCT_LOG_LEVEL=DEBUG

# Database
CCT_DB_PATH=database/cct_memory.db
CCT_PRICING_PATH=database/datasets

# Model
CCT_DEFAULT_MODEL=claude-3-5-sonnet-20240620
CCT_LLM_PROVIDER=gemini
GEMINI_API_KEY=your_dev_key

# Performance (fast iteration)
CCT_MAX_THOUGHTS=50
CCT_MAX_CONTENT_LENGTH=4000
CCT_MAX_CONTEXT_TOKENS=2000
CCT_CONTEXT_STRATEGY=sliding
CCT_TP_THRESHOLD=0.8
```

### Production Setup

```env
# Server Settings
CCT_SERVER_NAME=prod-cct-server
CCT_TRANSPORT=sse
CCT_HOST=0.0.0.0
CCT_PORT=8001
CCT_MAX_SESSIONS=500

# Logging
CCT_LOG_LEVEL=WARNING

# Database
CCT_DB_PATH=/var/lib/cct/cct_memory.db
CCT_PRICING_PATH=/etc/cct/pricing

# Model
CCT_DEFAULT_MODEL=claude-3-5-sonnet-20240620
CCT_LLM_PROVIDER=gemini
GEMINI_API_KEY=your_prod_key

# Performance (balanced)
CCT_MAX_THOUGHTS=200
CCT_MAX_CONTENT_LENGTH=8000
CCT_MAX_CONTEXT_TOKENS=4000
CCT_CONTEXT_STRATEGY=summarized
CCT_TP_THRESHOLD=0.9
```

### Multi-Agent Setup

```env
# Server Settings
CCT_SERVER_NAME=multi-agent-cct
CCT_TRANSPORT=sse
CCT_HOST=0.0.0.0
CCT_PORT=8001
CCT_MAX_SESSIONS=1000

# Logging
CCT_LOG_LEVEL=INFO

# Database
CCT_DB_PATH=/var/lib/cct/cct_memory.db
CCT_PRICING_PATH=/etc/cct/pricing

# Model
CCT_DEFAULT_MODEL=gpt-4o
CCT_LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_key

# Performance (optimized for concurrent access)
CCT_MAX_THOUGHTS=150
CCT_MAX_CONTENT_LENGTH=6000
CCT_MAX_CONTEXT_TOKENS=3000
CCT_CONTEXT_STRATEGY=summarized
CCT_TP_THRESHOLD=0.85
```

### Local Offline Setup

```env
# Server Settings
CCT_SERVER_NAME=local-cct-server
CCT_TRANSPORT=stdio
CCT_HOST=127.0.0.1
CCT_PORT=8000
CCT_MAX_SESSIONS=5

# Logging
CCT_LOG_LEVEL=DEBUG

# Database
CCT_DB_PATH=database/cct_memory.db
CCT_PRICING_PATH=database/datasets

# Model (Local Ollama)
CCT_DEFAULT_MODEL=llama2
CCT_LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434

# Performance (local optimization)
CCT_MAX_THOUGHTS=100
CCT_MAX_CONTENT_LENGTH=6000
CCT_MAX_CONTEXT_TOKENS=2000
CCT_CONTEXT_STRATEGY=sliding
CCT_TP_THRESHOLD=0.8
```

---

## Troubleshooting Configuration

### Common Issues

**Issue: Server won't start after changing .env**
- Check for syntax errors in `.env`
- Ensure no trailing spaces after values
- Verify environment variable names are correct
- Restart server after changes

**Issue: API key not working**
- Verify API key is correct
- Check provider's status page
- Ensure key has necessary permissions
- Test API key with provider's tools

**Issue: Model not recognized**
- Verify model ID matches pricing directory
- Check that pricing file exists
- Ensure model is available in your region
- Restart server after adding new models

**Issue: Port already in use**
- Change `CCT_PORT` to different value
- Check what's using the port: `netstat` or `lsof`
- Stop conflicting service
- Use port scanning tool to find available port

### Validation

Before deploying, validate your configuration:

```bash
# Check .env syntax
cat .env | grep -v '^#' | grep -v '^$' | grep '='

# Test database path
ls -la $(grep CCT_DB_PATH .env | cut -d'=' -f2)

# Test pricing path
ls -la $(grep CCT_PRICING_PATH .env | cut -d'=' -f2)

# Check API key format (should not be empty)
grep _API_KEY .env
```

---

## Summary

**Key Configuration Points:**
1. **Transport Mode**: Choose `stdio` for single IDE, `sse` for multi-agent
2. **LLM Provider**: Select based on speed, quality, and cost requirements
3. **API Keys**: Securely configure and regularly rotate
4. **Performance**: Tune based on use case (dev vs production)
5. **Security**: Use restrictive settings for production

**Best Practices:**
- Never commit `.env` to version control
- Use environment-specific configuration files
- Monitor costs when increasing context/thought limits
- Test configuration changes in development first
- Keep API keys secure and rotate regularly
- Backup database regularly
- Monitor server resources and adjust accordingly

**Getting Help:**
- Check `.env.example` for latest configuration options
- Review logs for configuration-related errors
- Consult documentation for specific features
- Report issues on GitHub with configuration details
