/**
 * RAG System - Type Definitions
 * Lightweight knowledge retrieval for AI chat
 */

export interface GlossaryTerm {
  en: string;
  th: string;
  definition: string;
  unit?: string;
  typical_range?: string;
  data_column?: string[];
  formula?: string;
  target?: string;
  threshold?: string;
  alert_type?: string;
  values?: string[];
  nominal?: string;
  upper_limit?: string;
  lower_limit?: string;
  nominal_voltage?: string;
  voltage?: string;
  typical_capacity?: string;
  voltage_ratio?: string;
  website?: string;
  impact?: string;
  horizon?: string;
  update_frequency?: string;
  use_case?: string;
  related?: string[];
}

export interface GlossaryData {
  version: string;
  last_updated: string;
  language: string[];
  terms: Record<string, GlossaryTerm>;
  acronyms?: Record<string, string>;
}

export interface KnowledgeContext {
  terms: Array<{
    key: string;
    term: GlossaryTerm;
    relevance: number;
  }>;
  acronyms: Array<{
    key: string;
    value: string;
  }>;
}

export interface RAGConfig {
  maxResults?: number;
  minRelevance?: number;
  includeRelated?: boolean;
}
