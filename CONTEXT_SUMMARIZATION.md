# Context Summarization Feature

## Overview

The Cursor MCP Server now includes **automatic context summarization** that triggers when context usage reaches **85%** of the maximum. This prevents context overflow while maintaining important information.

## How It Works

### 1. Context Tracking

The server tracks character count across all operations:
- `read_file` - Tracks file content size
- `list_files` - Tracks file list size
- `search_code` - Tracks search results size
- Resources (`workspace_tree`, `workspace_summary`, `readme`) - Tracks resource content size

### 2. Threshold Detection

When context usage reaches **85%** of `MCP_CONTEXT_MAX_CHARS` (default: 100,000 chars), the server automatically summarizes content.

### 3. Summarization Strategies

#### Text Files (`read_file`)
- **Keeps**: First 20% (headers/intro), Last 20% (conclusions)
- **Summarizes**: Middle 60% (keeps key patterns: `def`, `class`, `import`, `# TODO`, `# FIXME`, control flow)
- **Result**: ~30% of original size with key information preserved

#### File Lists (`list_files`)
- **Groups**: Files by extension
- **Shows**: Counts per extension, top 10 files per group
- **Result**: Compact summary showing file distribution

#### Search Results (`search_code`)
- **Keeps**: Top 5 files by match count (max 10 matches per file)
- **Summarizes**: Other files (shows count only)
- **Result**: Focus on most relevant matches

### 4. Transparency

All summarized content includes metadata headers:
```
[AUTO-SUMMARIZED at 85.0% context usage: file:path/to/file.py]
[Original: 50,000 chars → Summary: 15,000 chars (30.0%)]
```

## Configuration

### Environment Variables

```bash
# Max context size (default: 100,000 chars)
export MCP_CONTEXT_MAX_CHARS=150000

# Threshold for summarization (default: 0.85 = 85%)
export MCP_CONTEXT_SUMMARY_THRESHOLD=0.90

# Enable/disable summarization (default: true)
export MCP_CONTEXT_SUMMARY_ENABLED=true
```

### Programmatic Control

Use the `reset_context` tool to manually reset the context tracker after large operations:

```python
await reset_context()
# Returns: {"status": "reset", "previous_chars": 85000, "current_chars": 0}
```

## Monitoring

Check context usage via `get_diagnostics`:

```json
{
  "context": {
    "max_chars": 100000,
    "current_chars": 85000,
    "usage_pct": 85.0,
    "summary_threshold": 0.85,
    "summarization_enabled": true,
    "recent_summaries": [
      {
        "ts": 1234567890.123,
        "original_chars": 50000,
        "summary_chars": 15000,
        "compression_ratio": 0.3
      }
    ]
  }
}
```

## Benefits

1. **Prevents Context Overflow**: Automatically manages context size
2. **Preserves Key Information**: Keeps important patterns and sections
3. **Transparent**: Shows what was summarized and why
4. **Configurable**: Adjust thresholds and limits per use case
5. **Non-Destructive**: Original content still accessible via direct file reads

## Example Scenarios

### Scenario 1: Large Codebase Search

```python
# Search across large codebase
results = await search_code("TODO", file_glob="**/*.py", max_results=500)

# If context reaches 85%, automatically:
# - Keeps top 5 files with most matches
# - Summarizes other files (shows count only)
# - Adds metadata header explaining summarization
```

### Scenario 2: Reading Large Files

```python
# Read large file
content = await read_file("large_file.py")

# If context reaches 85%, automatically:
# - Keeps first 20% (headers, imports)
# - Keeps last 20% (conclusions, main functions)
# - Summarizes middle 60% (keeps key patterns)
# - Adds metadata header
```

### Scenario 3: Listing Many Files

```python
# List all files
files = await list_files(".", pattern="**/*", max_results=5000)

# If context reaches 85%, automatically:
# - Groups by extension
# - Shows counts per extension
# - Shows top 10 files per group
# - Adds metadata header
```

## Best Practices

1. **Monitor Usage**: Regularly check `get_diagnostics` to see context usage
2. **Reset After Large Ops**: Use `reset_context` after processing large datasets
3. **Adjust Thresholds**: Increase `MCP_CONTEXT_MAX_CHARS` for larger projects
4. **Disable if Needed**: Set `MCP_CONTEXT_SUMMARY_ENABLED=false` to disable
5. **Review Summaries**: Check metadata headers to understand what was summarized

## Technical Details

### Implementation

- **ContextTracker Class**: Tracks usage and manages summarization
- **Global Tracker**: Single instance shared across all tools
- **Deque for History**: Keeps last 10 summarization events
- **Smart Summarization**: Pattern-based text reduction
- **Audit Integration**: Summarization events logged in audit log

### Performance

- **Minimal Overhead**: Character counting is O(1) per operation
- **Lazy Summarization**: Only summarizes when threshold reached
- **Efficient Patterns**: Regex patterns compiled once
- **Memory Efficient**: Summaries replace original content in tracker

## Future Enhancements

Potential improvements:
- Token-based tracking (more accurate for LLMs)
- Per-file summarization history
- Custom summarization strategies per file type
- Compression ratio optimization
- Context window prediction

