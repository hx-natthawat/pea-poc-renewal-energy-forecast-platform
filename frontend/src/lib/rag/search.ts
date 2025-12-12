/**
 * RAG System - Keyword Search Engine
 * Simple but effective keyword matching for knowledge retrieval
 */

import { loadGlossary } from "./loader";
import type { GlossaryTerm, KnowledgeContext, RAGConfig } from "./types";

/**
 * Extract keywords from user query
 * Handles both English and Thai text
 */
export function extractKeywords(query: string): string[] {
  // Convert to lowercase for case-insensitive matching
  const normalized = query.toLowerCase();

  // Split on word boundaries, filter out common words
  const commonWords = new Set([
    // English
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "from",
    "is",
    "are",
    "was",
    "were",
    "what",
    "how",
    "why",
    "when",
    "where",
    "can",
    "could",
    "should",
    "would",
    // Thai common words
    "คือ",
    "เป็น",
    "อะไร",
    "ที่",
    "และ",
    "หรือ",
    "ใน",
    "ของ",
  ]);

  const words = normalized
    .split(/[\s,;.!?(){}[\]]+/)
    .filter((word) => word.length > 2 && !commonWords.has(word));

  return words;
}

/**
 * Calculate relevance score for a term
 */
function calculateRelevance(keywords: string[], termKey: string, term: GlossaryTerm): number {
  let score = 0;

  // Check term key match
  const normalizedKey = termKey.toLowerCase();
  for (const keyword of keywords) {
    if (normalizedKey.includes(keyword) || keyword.includes(normalizedKey)) {
      score += 10; // Exact key match is highly relevant
    }
  }

  // Check English name
  const enLower = term.en.toLowerCase();
  for (const keyword of keywords) {
    if (enLower.includes(keyword) || keyword.includes(enLower)) {
      score += 5;
    }
  }

  // Check Thai name
  const thLower = term.th.toLowerCase();
  for (const keyword of keywords) {
    if (thLower.includes(keyword) || keyword.includes(thLower)) {
      score += 5;
    }
  }

  // Check definition
  const defLower = term.definition.toLowerCase();
  for (const keyword of keywords) {
    if (defLower.includes(keyword)) {
      score += 2;
    }
  }

  // Check data columns if present
  if (term.data_column) {
    for (const col of term.data_column) {
      const colLower = col.toLowerCase();
      for (const keyword of keywords) {
        if (colLower.includes(keyword) || keyword.includes(colLower)) {
          score += 3;
        }
      }
    }
  }

  return score;
}

/**
 * Search glossary for relevant terms
 */
export function searchKnowledge(query: string, config: RAGConfig = {}): KnowledgeContext {
  const { maxResults = 5, minRelevance = 2, includeRelated = true } = config;

  const keywords = extractKeywords(query);
  const glossary = loadGlossary();

  // Score all terms
  const scoredTerms: Array<{
    key: string;
    term: GlossaryTerm;
    relevance: number;
  }> = [];

  for (const [key, term] of Object.entries(glossary.terms)) {
    const relevance = calculateRelevance(keywords, key, term);
    if (relevance >= minRelevance) {
      scoredTerms.push({ key, term, relevance });
    }
  }

  // Sort by relevance (highest first)
  scoredTerms.sort((a, b) => b.relevance - a.relevance);

  // Take top results
  const results = scoredTerms.slice(0, maxResults);

  // Optionally include related terms
  if (includeRelated && results.length > 0) {
    const relatedKeys = new Set<string>();
    const existingKeys = new Set(results.map((r) => r.key));

    for (const result of results) {
      if (result.term.related) {
        for (const related of result.term.related) {
          if (!existingKeys.has(related) && glossary.terms[related]) {
            relatedKeys.add(related);
          }
        }
      }
    }

    // Add related terms with lower relevance
    for (const key of relatedKeys) {
      if (results.length >= maxResults * 2) break; // Limit total results
      results.push({
        key,
        term: glossary.terms[key],
        relevance: 1, // Lower relevance for related terms
      });
    }
  }

  // Search acronyms
  const acronyms: Array<{ key: string; value: string }> = [];
  if (glossary.acronyms) {
    for (const [key, value] of Object.entries(glossary.acronyms)) {
      const keyLower = key.toLowerCase();
      const valueLower = value.toLowerCase();

      for (const keyword of keywords) {
        if (
          keyLower.includes(keyword) ||
          keyword.includes(keyLower) ||
          valueLower.includes(keyword)
        ) {
          acronyms.push({ key, value });
          break;
        }
      }
    }
  }

  return {
    terms: results,
    acronyms,
  };
}
