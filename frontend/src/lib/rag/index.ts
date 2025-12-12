/**
 * RAG System - Main Entry Point
 * Lightweight knowledge retrieval for AI chat
 */

export { enhanceSystemPrompt, formatContext } from "./formatter";
export { clearGlossaryCache, loadGlossary } from "./loader";
export { extractKeywords, searchKnowledge } from "./search";
export type {
  GlossaryData,
  GlossaryTerm,
  KnowledgeContext,
  RAGConfig,
} from "./types";

/**
 * Main RAG function - retrieves and formats knowledge for a query
 *
 * @param query - User's question or message
 * @param language - Language for formatting ("en" or "th")
 * @returns Formatted context string ready for injection into system prompt
 *
 * @example
 * ```typescript
 * const context = retrieveKnowledge("What is MAPE?", "en");
 * const enhancedPrompt = `${basePrompt}\n\n${context}`;
 * ```
 */
export function retrieveKnowledge(query: string, language: "en" | "th" = "th"): string {
  const { searchKnowledge } = require("./search");
  const { formatContext } = require("./formatter");

  const context = searchKnowledge(query, {
    maxResults: 5,
    minRelevance: 2,
    includeRelated: true,
  });

  return formatContext(context, language);
}
