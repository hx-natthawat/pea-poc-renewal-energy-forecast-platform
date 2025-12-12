# RAG System Usage Guide

**Audience**: Developers, System Administrators
**Prerequisites**: Basic understanding of the PEA RE Forecast Platform
**Version**: 1.0

## Overview

This guide explains how to use and maintain the Retrieval Augmented Generation (RAG) system in the PEA RE Forecast Platform. The RAG system enhances AI chat responses with domain-specific knowledge about solar forecasting, voltage prediction, and grid operations.

## How It Works (Simple Explanation)

When a user asks a question in the AI chat:

1. The system **extracts keywords** from the question (e.g., "MAPE", "voltage", "prosumer")
2. It **searches the knowledge base** (YAML files) for matching terms
3. It **injects relevant definitions** into the AI's system prompt
4. The AI provides a **more accurate, domain-specific answer**

**Example**:

```
User: "What is MAPE and why is it important?"

Without RAG:
AI: "MAPE is a statistical measure..." (generic answer)

With RAG:
AI: "MAPE (Mean Absolute Percentage Error) is an accuracy metric used in the PEA RE Forecast Platform to measure solar power prediction accuracy. Our target is MAPE < 10%, calculated as mean(|actual - predicted| / actual) × 100..." (domain-specific answer)
```

## For Developers

### Quick Start

The RAG system is automatically integrated into the `/api/chat` route. No setup required!

### Using RAG in Your Code

#### Basic Search

```typescript
import { searchKnowledge } from "@/lib/rag";

const context = searchKnowledge("What is MAPE?");

console.log(context.terms);
// [{
//   key: "mape",
//   term: {
//     en: "Mean Absolute Percentage Error",
//     th: "ค่าความคลาดเคลื่อนสัมบูรณ์เฉลี่ยร้อยละ",
//     definition: "Accuracy metric for forecasts",
//     target: "< 10%",
//     ...
//   },
//   relevance: 10
// }]
```

#### Advanced Search with Options

```typescript
const context = searchKnowledge("voltage prediction accuracy", {
  maxResults: 3,          // Return max 3 terms
  minRelevance: 5,        // Only terms with score >= 5
  includeRelated: false,  // Don't include related terms
});
```

#### Format Context for Display

```typescript
import { formatContext } from "@/lib/rag";

const markdown = formatContext(context, "th"); // or "en"

// Returns formatted markdown:
// ## ความรู้ที่เกี่ยวข้อง
// ### คำศัพท์เทคนิค:
// ...
```

#### Enhance System Prompt

```typescript
import { enhanceSystemPrompt } from "@/lib/rag";

const basePrompt = "You are a helpful AI assistant...";
const enhanced = enhanceSystemPrompt(basePrompt, context, "th");

// The enhanced prompt now includes relevant knowledge
```

### Testing Your Changes

```bash
# Run RAG tests
npm run test -- src/lib/rag

# Run specific test file
npm run test -- src/lib/rag/search.test.ts

# Watch mode for development
npm run test -- src/lib/rag --watch
```

### Debugging

Enable debug logging:

```bash
RAG_DEBUG=true npm run dev
```

View logs in browser console or terminal.

## For Content Managers

### Adding New Terms to the Knowledge Base

#### Step 1: Open the Glossary File

File: `docs/knowledge-base/domain/glossary.yaml`

```bash
# Using your favorite editor
code docs/knowledge-base/domain/glossary.yaml
```

#### Step 2: Add Your Term

```yaml
terms:
  your_new_term:
    en: "English Name"
    th: "ชื่อภาษาไทย"
    definition: "Clear, concise definition of the term"
    unit: "kW"                    # Optional
    typical_range: "0 to 5000"    # Optional
    target: "< 10%"               # Optional
    related: ["related_term1"]    # Optional
```

#### Step 3: Complete Example

```yaml
grid_stability:
  en: "Grid Stability"
  th: "ความเสถียรของระบบไฟฟ้า"
  definition: "The ability of the electrical grid to maintain steady voltage and frequency under varying load conditions"
  related: ["voltage_limit", "frequency", "load_balancing"]
```

#### Step 4: Commit Your Changes

```bash
git add docs/knowledge-base/domain/glossary.yaml
git commit -m "Add grid_stability term to glossary"
git push
```

The changes will be live after the next deployment!

### Updating Existing Terms

Just edit the YAML file and follow the same commit process.

### Adding Acronyms

```yaml
acronyms:
  NEW_ACRONYM: "Full Name (ชื่อเต็ม)"
  DER: "Distributed Energy Resources (ทรัพยากรพลังงานกระจาย)"
```

### Best Practices for Term Definitions

✅ **Do**:
- Write clear, concise definitions (1-2 sentences)
- Include both English and Thai names
- Add units and ranges when applicable
- Link related terms
- Use consistent terminology

❌ **Don't**:
- Write long paragraphs (keep it short!)
- Use jargon without explanation
- Forget bilingual support
- Leave required fields empty

## For System Administrators

### Monitoring RAG Performance

#### Check Logs

```bash
# Development
npm run dev
# Watch for: "RAG enhanced prompt with X terms"

# Production
docker logs pea-frontend | grep RAG
```

#### Performance Metrics

Normal RAG overhead: **15-30ms per request**

If you see higher latency:
1. Check glossary file size (should be < 1MB)
2. Clear cache and restart: `clearGlossaryCache()`
3. Review number of terms (optimal: < 500)

### Cache Management

The glossary is cached in memory after first load.

**Clear cache** (development only):

```typescript
import { clearGlossaryCache } from "@/lib/rag";
clearGlossaryCache();
```

**Cache refreshes automatically**:
- On server restart
- On new deployment
- When glossary file is modified (in dev mode)

### Troubleshooting

#### Issue: RAG not returning results

**Symptoms**: AI responses don't include domain knowledge

**Diagnosis**:
```bash
# Check if glossary file exists
ls -lh docs/knowledge-base/domain/glossary.yaml

# Validate YAML syntax
npx js-yaml docs/knowledge-base/domain/glossary.yaml
```

**Solution**:
1. Verify file path is correct
2. Check YAML syntax (no tabs, proper indentation)
3. Restart development server
4. Check browser console for errors

#### Issue: Wrong terms retrieved

**Symptoms**: Irrelevant terms appear in context

**Diagnosis**: Relevance threshold too low

**Solution**:
```typescript
// In route.ts, increase minRelevance
const context = searchKnowledge(query, {
  maxResults: 5,
  minRelevance: 5,  // Increase from 2 to 5
  includeRelated: true,
});
```

#### Issue: Missing Thai translations

**Symptoms**: Thai terms not found

**Diagnosis**: Glossary missing Thai (`th`) field

**Solution**: Add Thai translation to all terms in `glossary.yaml`

### Backup and Recovery

#### Backup Glossary

```bash
# Backup before making changes
cp docs/knowledge-base/domain/glossary.yaml \
   docs/knowledge-base/domain/glossary.yaml.backup
```

#### Restore from Backup

```bash
# If something goes wrong
cp docs/knowledge-base/domain/glossary.yaml.backup \
   docs/knowledge-base/domain/glossary.yaml
```

### Deployment Checklist

Before deploying changes to production:

- [ ] Validate YAML syntax
- [ ] Test all new terms locally
- [ ] Run unit tests: `npm run test`
- [ ] Check performance in dev mode
- [ ] Review term definitions for accuracy
- [ ] Commit changes with clear message
- [ ] Deploy during maintenance window

## Common Use Cases

### 1. Adding Support for New Domain

**Scenario**: Platform adds battery storage forecasting

**Steps**:
1. Create new terms:
   ```yaml
   battery_soc:
     en: "State of Charge"
     th: "สถานะการชาร์จ"
     definition: "Percentage of battery capacity currently stored"
     unit: "%"
     typical_range: "0 to 100"

   battery_soh:
     en: "State of Health"
     th: "สถานะความแข็งแรงของแบตเตอรี่"
     definition: "Measure of battery degradation over time"
     unit: "%"
     typical_range: "0 to 100"
   ```

2. Add related terms and update existing ones
3. Test with sample queries
4. Deploy

### 2. Improving Search Results

**Scenario**: Users ask about "PV panels" but RAG doesn't find it

**Solution**: Add synonym or update existing term

```yaml
pv_panel:
  en: "PV Panel"
  th: "แผงโซลาร์"
  definition: "Photovoltaic panel that converts sunlight to electricity"
  related: ["pv_temperature", "irradiance", "power_output"]
  # Add common variations in definition
  # "PV panel, solar panel, photovoltaic module"
```

### 3. Multilingual Support

**Scenario**: Support English-speaking operators

**Current**: RAG already supports both languages!

```typescript
// Thai query
const contextTH = searchKnowledge("แรงดันเกินคืออะไร");

// English query
const contextEN = searchKnowledge("What is overvoltage?");

// Both return the same term with bilingual content
```

## FAQ

### Q: Can I use vector embeddings instead of keyword matching?

**A**: Not yet. The current implementation uses keyword matching for simplicity and performance. Vector embeddings may be added in Phase 4 if needed.

### Q: How many terms can the knowledge base handle?

**A**: Optimal range is 100-500 terms. Current: 50+ terms. System can scale to ~1000 terms before performance degrades.

### Q: Can I add images or diagrams to terms?

**A**: Not in the current version. Terms are text-only. Consider linking to documentation with images.

### Q: How do I add context from documentation files?

**A**: Phase 2 will support document chunking and search. For now, extract key information into glossary terms.

### Q: What if two terms have the same keyword?

**A**: Both will be retrieved and ranked by relevance. The formatter includes both in the context.

### Q: Can I disable RAG for specific queries?

**A**: Yes, RAG gracefully falls back to base prompt if search fails or returns no results.

## References

- Architecture Documentation: `docs/architecture/rag-system.md`
- Source Code: `frontend/src/lib/rag/`
- Knowledge Base: `docs/knowledge-base/domain/glossary.yaml`
- Tests: `frontend/src/lib/rag/*.test.ts`

## Support

For questions or issues:
1. Check this guide first
2. Review architecture documentation
3. Run tests to verify functionality
4. Contact the development team

---

**Last Updated**: 2025-12-12
**Version**: 1.0
**Maintainer**: Development Team
