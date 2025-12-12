# RAG System

Lightweight Retrieval Augmented Generation for the PEA RE Forecast Platform AI Chat.

## Quick Start

```typescript
import { searchKnowledge, enhanceSystemPrompt } from "@/lib/rag";

// Search for relevant knowledge
const context = searchKnowledge("What is MAPE?");

// Enhance system prompt with context
const enhanced = enhanceSystemPrompt(basePrompt, context, "th");
```

## Features

- ✅ **Keyword-based search** (no vector embeddings needed)
- ✅ **Bilingual support** (English and Thai)
- ✅ **Fast** (sub-30ms latency)
- ✅ **Cached** (knowledge base loaded once)
- ✅ **Simple** (YAML knowledge base)
- ✅ **Tested** (comprehensive unit tests)

## Architecture

```
User Query → Extract Keywords → Search Glossary → Rank Results → Format Context → Enhance Prompt → LLM
```

## Files

| File | Purpose |
|------|---------|
| `types.ts` | TypeScript interfaces |
| `loader.ts` | YAML knowledge base loader |
| `search.ts` | Keyword extraction and search |
| `formatter.ts` | Context formatting for LLM |
| `index.ts` | Main entry point |
| `*.test.ts` | Unit tests |

## Usage Examples

### Basic Search

```typescript
import { searchKnowledge } from "@/lib/rag";

const context = searchKnowledge("voltage limit prosumer");

console.log(context.terms);
// [{
//   key: "voltage_limit",
//   term: { en: "Voltage Limit", th: "ขีดจำกัดแรงดัน", ... },
//   relevance: 8
// }]

console.log(context.acronyms);
// [{ key: "PEA", value: "Provincial Electricity Authority" }]
```

### Advanced Search

```typescript
const context = searchKnowledge("solar forecast accuracy", {
  maxResults: 3,          // Max 3 terms
  minRelevance: 5,        // Min score 5
  includeRelated: false,  // No related terms
});
```

### Format Context

```typescript
import { formatContext } from "@/lib/rag";

const markdown = formatContext(context, "th");
// Returns formatted markdown for injection
```

### Enhance System Prompt

```typescript
import { enhanceSystemPrompt } from "@/lib/rag";

const base = "You are an AI assistant...";
const enhanced = enhanceSystemPrompt(base, context, "en");
// Returns prompt with injected knowledge
```

## Configuration

```typescript
interface RAGConfig {
  maxResults?: number;      // Default: 5
  minRelevance?: number;    // Default: 2
  includeRelated?: boolean; // Default: true
}
```

## Knowledge Base

Located at: `docs/knowledge-base/domain/glossary.yaml`

```yaml
terms:
  mape:
    en: "Mean Absolute Percentage Error"
    th: "ค่าความคลาดเคลื่อนสัมบูรณ์เฉลี่ยร้อยละ"
    definition: "Accuracy metric for forecasts"
    target: "< 10%"
    related: ["rmse", "mae"]

acronyms:
  MAPE: "Mean Absolute Percentage Error"
```

## Search Algorithm

### Keyword Extraction

1. Normalize to lowercase
2. Split on word boundaries
3. Filter common words (the, a, is, คือ, etc.)
4. Return words > 2 characters

### Relevance Scoring

| Match Type | Score |
|-----------|-------|
| Exact key match | +10 |
| English name | +5 |
| Thai name | +5 |
| Data column | +3 |
| Definition | +2 |

### Ranking

Terms are sorted by relevance (highest first), then top N results are returned.

## Testing

```bash
# Run all tests
npm run test -- src/lib/rag

# Run specific test
npm run test -- src/lib/rag/search.test.ts

# Watch mode
npm run test -- src/lib/rag --watch

# Coverage
npm run test -- src/lib/rag --coverage
```

## Performance

| Operation | Time |
|-----------|------|
| First load | ~10-20ms |
| Cached load | 0ms |
| Search | ~5-10ms |
| Format | ~1-2ms |
| **Total** | **~15-30ms** |

## Adding New Terms

Edit `docs/knowledge-base/domain/glossary.yaml`:

```yaml
new_term:
  en: "English Name"
  th: "ชื่อภาษาไทย"
  definition: "Clear definition"
  unit: "kW"                    # Optional
  related: ["other_term"]       # Optional
```

Commit and deploy. Cache refreshes automatically.

## Troubleshooting

### No results returned

1. Check glossary file exists
2. Validate YAML syntax
3. Clear cache: `clearGlossaryCache()`
4. Check keyword extraction

### Wrong results

1. Increase `minRelevance` threshold
2. Review term definitions
3. Add more specific terms to glossary

### Performance issues

1. Check glossary size (should be < 1MB)
2. Reduce `maxResults`
3. Disable `includeRelated`

## API Reference

### `searchKnowledge(query, config?)`

Search knowledge base for relevant terms.

**Parameters**:
- `query: string` - User's question
- `config?: RAGConfig` - Optional configuration

**Returns**: `KnowledgeContext` with terms and acronyms

### `extractKeywords(query)`

Extract keywords from query string.

**Parameters**:
- `query: string` - Input text

**Returns**: `string[]` - Array of keywords

### `formatContext(context, language?)`

Format knowledge context as markdown.

**Parameters**:
- `context: KnowledgeContext` - Search results
- `language?: "en" | "th"` - Output language (default: "th")

**Returns**: `string` - Formatted markdown

### `enhanceSystemPrompt(basePrompt, context, language?)`

Inject context into system prompt.

**Parameters**:
- `basePrompt: string` - Original prompt
- `context: KnowledgeContext` - Search results
- `language?: "en" | "th"` - Output language (default: "th")

**Returns**: `string` - Enhanced prompt

### `loadGlossary()`

Load knowledge base from YAML file.

**Returns**: `GlossaryData`

### `clearGlossaryCache()`

Clear the in-memory cache.

**Returns**: `void`

## Documentation

- [Architecture Documentation](../../../../docs/architecture/rag-system.md)
- [Usage Guide](../../../../docs/guides/rag-usage-guide.md)
- [Knowledge Base](../../../../docs/knowledge-base/domain/glossary.yaml)

## License

Part of the PEA RE Forecast Platform
