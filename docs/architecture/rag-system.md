# RAG System Architecture

**Version**: 1.0
**Status**: Active
**Created**: 2025-12-12
**Last Updated**: 2025-12-12

## Overview

The PEA RE Forecast Platform implements a lightweight Retrieval Augmented Generation (RAG) system to enhance the AI Chat feature with domain-specific knowledge. This document describes the architecture, implementation, and usage of the RAG system.

## Purpose

The RAG system provides:

1. **Domain Knowledge Injection**: Automatically injects relevant technical terms and definitions into AI chat responses
2. **Bilingual Support**: Handles both English and Thai queries and responses
3. **Zero External Dependencies**: Uses keyword matching instead of vector embeddings (no vector DB needed)
4. **Performance**: Fast, cached knowledge base loading with minimal latency

## Architecture

### High-Level Flow

```
User Query
    ↓
Extract Keywords
    ↓
Search Knowledge Base (YAML files)
    ↓
Match Terms & Acronyms
    ↓
Format Context
    ↓
Inject into System Prompt
    ↓
LLM (Claude 3.5 Sonnet)
    ↓
Enhanced Response
```

### Component Structure

```
frontend/src/lib/rag/
├── types.ts          # TypeScript interfaces
├── loader.ts         # YAML knowledge base loader (with cache)
├── search.ts         # Keyword extraction & search engine
├── formatter.ts      # Context formatting for LLM
├── index.ts          # Main entry point
├── search.test.ts    # Unit tests for search
└── formatter.test.ts # Unit tests for formatter
```

### Data Flow

1. **User sends message** → `/api/chat` route
2. **Extract keywords** from last user message
3. **Search glossary** for matching terms
4. **Rank results** by relevance score
5. **Format context** in structured markdown
6. **Enhance system prompt** by injecting context
7. **Send to LLM** with enhanced prompt
8. **Stream response** back to user

## Knowledge Base

### Structure

```
docs/knowledge-base/
├── index.yaml              # Master configuration
├── taxonomy.yaml           # Classification system
└── domain/
    └── glossary.yaml       # 50+ technical terms (en/th)
```

### Glossary Schema

```yaml
terms:
  mape:
    en: "Mean Absolute Percentage Error"
    th: "ค่าความคลาดเคลื่อนสัมบูรณ์เฉลี่ยร้อยละ"
    definition: "Accuracy metric for forecasts"
    formula: "mean(|actual - predicted| / actual) × 100"
    target: "< 10%"
    related: ["rmse", "r_squared"]

acronyms:
  PEA: "Provincial Electricity Authority (การไฟฟ้าส่วนภูมิภาค)"
  MAPE: "Mean Absolute Percentage Error"
```

## Search Algorithm

### Keyword Extraction

```typescript
extractKeywords(query: string): string[]
```

1. Convert to lowercase
2. Split on word boundaries
3. Filter out common words (the, a, is, คือ, เป็น, etc.)
4. Return words with length > 2

### Relevance Scoring

Terms are scored based on keyword matches:

| Match Location | Score |
|---------------|-------|
| Term key (exact) | +10 |
| English name | +5 |
| Thai name | +5 |
| Data column | +3 |
| Definition | +2 |
| Related term | +1 (added separately) |

### Configuration Options

```typescript
interface RAGConfig {
  maxResults?: number;      // Default: 5
  minRelevance?: number;    // Default: 2
  includeRelated?: boolean; // Default: true
}
```

## Context Formatting

### Output Format

```markdown
## ความรู้ที่เกี่ยวข้อง (Relevant Knowledge)

### ตัวย่อ (Acronyms):
- **PEA**: Provincial Electricity Authority (การไฟฟ้าส่วนภูมิภาค)
- **MAPE**: Mean Absolute Percentage Error

### คำศัพท์เทคนิค (Technical Terms):

#### Mean Absolute Percentage Error (ค่าความคลาดเคลื่อนสัมบูรณ์เฉลี่ยร้อยละ)
**Definition**: Accuracy metric for forecasts, expressed as percentage
**Formula**: mean(|actual - predicted| / actual) × 100
**Target**: < 10%
**Related**: rmse, r_squared
```

### Injection Strategy

Context is injected **before** the "Guidelines" section of the system prompt:

```
[Base Prompt Header]
...
[Platform Capabilities]

## ความรู้ที่เกี่ยวข้อง     ← RAG context injected here
[Retrieved terms and acronyms]

## แนวทางการตอบ             ← Existing guidelines
...
```

## API Integration

### Chat Route Changes

**File**: `frontend/src/app/api/chat/route.ts`

```typescript
import { searchKnowledge, enhanceSystemPrompt } from "@/lib/rag";

// Extract last user message
const lastUserMessage = messages
  .filter((m) => m.role === "user")
  .pop();

// Search knowledge base
const context = searchKnowledge(lastUserMessage.content, {
  maxResults: 5,
  minRelevance: 2,
  includeRelated: true,
});

// Enhance system prompt
const systemPrompt = enhanceSystemPrompt(
  basePrompt,
  context,
  language === "th" ? "th" : "en"
);
```

## Performance Characteristics

### Latency

| Operation | Time |
|-----------|------|
| First load (read YAML) | ~10-20ms |
| Subsequent loads (cached) | ~0ms |
| Keyword extraction | ~1ms |
| Knowledge search | ~5-10ms |
| Context formatting | ~1-2ms |
| **Total RAG overhead** | **~15-30ms** |

### Memory

- Glossary cache: ~50KB
- Per-request overhead: ~5KB

### Scalability

- No database required
- No network calls
- Stateless operation
- Horizontally scalable

## Advantages of This Approach

### 1. Simplicity
- No vector database (Pinecone, Qdrant, etc.)
- No embedding models
- No complex infrastructure

### 2. Performance
- Sub-30ms latency
- In-memory cached knowledge
- No external API calls

### 3. Maintainability
- Knowledge base is human-readable YAML
- Easy to update and version control
- No reindexing required

### 4. Cost
- Zero additional infrastructure costs
- No embedding API costs
- No vector DB hosting fees

### 5. Accuracy
- Keyword matching works well for technical terms
- Bilingual support without translation
- Deterministic results (no semantic drift)

## Limitations & Trade-offs

### 1. Semantic Understanding
❌ Cannot handle synonyms or paraphrases
✅ Mitigated by: Including common variations in glossary

### 2. Scale
❌ Performance degrades with very large knowledge bases (>10,000 terms)
✅ Current: 50+ terms, room for 100x growth

### 3. Context Relevance
❌ May retrieve tangentially related terms
✅ Mitigated by: Relevance threshold and ranking

## Future Enhancements

### Phase 2: Document Retrieval
- Add support for searching architectural docs
- Chunk and index markdown files
- Still using keyword matching

### Phase 3: Hybrid Search
- Add TF-IDF scoring
- Add BM25 algorithm
- Still no vector embeddings

### Phase 4: Vector Embeddings (Optional)
- Only if keyword matching proves insufficient
- Use OpenAI embeddings or local models
- Add vector similarity search

## Testing

### Unit Tests

```bash
npm run test -- src/lib/rag
```

### Test Coverage

- ✅ Keyword extraction (English, Thai, mixed)
- ✅ Term search with relevance scoring
- ✅ Acronym matching
- ✅ Related term inclusion
- ✅ Context formatting (bilingual)
- ✅ System prompt enhancement

### Example Queries Tested

| Query | Expected Results |
|-------|-----------------|
| "What is MAPE?" | MAPE term + related metrics |
| "แรงดันเกินคืออะไร" | overvoltage, voltage_limit |
| "prosumer network" | prosumer, phase, transformer |
| "solar irradiance" | irradiance, pyranometer, power_output |

## Usage Examples

### Basic Usage

```typescript
import { searchKnowledge } from "@/lib/rag";

const context = searchKnowledge("What is MAPE?");
console.log(context.terms); // [{ key: "mape", term: {...}, relevance: 10 }]
```

### With Configuration

```typescript
const context = searchKnowledge("voltage prediction accuracy", {
  maxResults: 3,
  minRelevance: 5,
  includeRelated: false,
});
```

### Formatting Only

```typescript
import { formatContext } from "@/lib/rag";

const formattedText = formatContext(context, "th");
// Returns markdown-formatted context
```

### Full Enhancement

```typescript
import { enhanceSystemPrompt } from "@/lib/rag";

const enhanced = enhanceSystemPrompt(basePrompt, context, "en");
// Returns system prompt with injected knowledge
```

## Monitoring & Debugging

### Logging

The RAG system logs to console:

```typescript
// Success
console.log("RAG enhanced prompt with", context.terms.length, "terms");

// Fallback
console.warn("RAG search failed, using base prompt:", error);
```

### Debug Mode

Set environment variable for verbose logging:

```bash
RAG_DEBUG=true npm run dev
```

## Maintenance

### Updating Knowledge Base

1. Edit `docs/knowledge-base/domain/glossary.yaml`
2. Add new terms or update existing ones
3. Commit changes to git
4. Cache automatically refreshes on next deployment

### Adding New Terms

```yaml
new_term:
  en: "English Name"
  th: "ชื่อภาษาไทย"
  definition: "Clear, concise definition"
  unit: "optional unit"
  related: ["related_term1", "related_term2"]
```

### Cache Management

```typescript
import { clearGlossaryCache } from "@/lib/rag";

// Clear cache (useful for testing)
clearGlossaryCache();
```

## Security Considerations

### Input Validation
- User queries are sanitized during keyword extraction
- No code injection possible (YAML is parsed, not executed)

### Rate Limiting
- RAG adds ~30ms per request
- No additional rate limiting needed
- Inherits chat API rate limits

### Data Privacy
- All knowledge is public (technical documentation)
- No sensitive data in glossary
- No user data stored in RAG system

## Deployment

### Requirements

```json
{
  "dependencies": {
    "yaml": "^2.3.4"
  }
}
```

### Build Configuration

No special build configuration needed. The system works in:
- Development mode (npm run dev)
- Production builds (npm run build)
- Edge runtime (Next.js API routes)

### Environment Variables

None required. All configuration is in code or YAML files.

## References

- Knowledge Base: `docs/knowledge-base/`
- Source Code: `frontend/src/lib/rag/`
- Tests: `frontend/src/lib/rag/*.test.ts`
- API Route: `frontend/src/app/api/chat/route.ts`

---

**Document Owner**: Backend Architect
**Review Cycle**: Quarterly
**Last Reviewed**: 2025-12-12
