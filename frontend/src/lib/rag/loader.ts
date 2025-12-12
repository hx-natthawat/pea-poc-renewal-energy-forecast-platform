/**
 * RAG System - Knowledge Base Loader
 * Loads and caches YAML knowledge base files
 */

import { readFileSync } from "node:fs";
import { join } from "node:path";
import { parse as parseYAML } from "yaml";
import type { GlossaryData } from "./types";

let glossaryCache: GlossaryData | null = null;

/**
 * Load glossary from YAML file
 * Cached after first load for performance
 */
export function loadGlossary(): GlossaryData {
  if (glossaryCache) {
    return glossaryCache;
  }

  try {
    // Try multiple paths to find the glossary file
    const possiblePaths = [
      join(process.cwd(), "docs", "knowledge-base", "domain", "glossary.yaml"),
      join(process.cwd(), "..", "docs", "knowledge-base", "domain", "glossary.yaml"),
    ];

    for (const path of possiblePaths) {
      try {
        const glossaryContent = readFileSync(path, "utf-8");
        glossaryCache = parseYAML(glossaryContent) as GlossaryData;
        return glossaryCache;
      } catch {
        // Try next path
      }
    }

    throw new Error("Glossary file not found in any expected location");
  } catch (error) {
    console.error("Failed to load glossary:", error);
    // Return empty glossary if file doesn't exist
    return {
      version: "1.0",
      last_updated: new Date().toISOString(),
      language: ["en", "th"],
      terms: {},
      acronyms: {},
    };
  }
}

/**
 * Clear the cache (useful for development/testing)
 */
export function clearGlossaryCache(): void {
  glossaryCache = null;
}
