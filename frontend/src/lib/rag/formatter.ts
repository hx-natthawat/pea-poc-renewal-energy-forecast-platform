/**
 * RAG System - Context Formatter
 * Formats retrieved knowledge into LLM-friendly context
 */

import type { KnowledgeContext } from "./types";

/**
 * Format knowledge context for injection into system prompt
 * Creates structured context that the LLM can understand
 */
export function formatContext(context: KnowledgeContext, language: "en" | "th" = "th"): string {
  if (context.terms.length === 0 && context.acronyms.length === 0) {
    return "";
  }

  const sections: string[] = [];

  // Add header
  if (language === "th") {
    sections.push("## ความรู้ที่เกี่ยวข้อง (Relevant Knowledge)");
  } else {
    sections.push("## Relevant Knowledge");
  }

  sections.push("");

  // Add acronyms if found
  if (context.acronyms.length > 0) {
    if (language === "th") {
      sections.push("### ตัวย่อ (Acronyms):");
    } else {
      sections.push("### Acronyms:");
    }

    for (const { key, value } of context.acronyms) {
      sections.push(`- **${key}**: ${value}`);
    }
    sections.push("");
  }

  // Add terms
  if (context.terms.length > 0) {
    if (language === "th") {
      sections.push("### คำศัพท์เทคนิค (Technical Terms):");
    } else {
      sections.push("### Technical Terms:");
    }
    sections.push("");

    for (const { term } of context.terms) {
      // Term header with both languages
      sections.push(`#### ${term.en} (${term.th})`);

      // Definition
      sections.push(`**Definition**: ${term.definition}`);

      // Add relevant metadata
      if (term.unit) {
        sections.push(`**Unit**: ${term.unit}`);
      }

      if (term.typical_range) {
        sections.push(`**Range**: ${term.typical_range}`);
      }

      if (term.target) {
        sections.push(`**Target**: ${term.target}`);
      }

      if (term.formula) {
        sections.push(`**Formula**: ${term.formula}`);
      }

      if (term.threshold) {
        sections.push(`**Threshold**: ${term.threshold}`);
      }

      if (term.alert_type) {
        sections.push(`**Alert Type**: ${term.alert_type}`);
      }

      if (term.nominal) {
        sections.push(`**Nominal**: ${term.nominal}`);
      }

      if (term.upper_limit) {
        sections.push(`**Upper Limit**: ${term.upper_limit}`);
      }

      if (term.lower_limit) {
        sections.push(`**Lower Limit**: ${term.lower_limit}`);
      }

      if (term.values) {
        sections.push(`**Values**: ${term.values.join(", ")}`);
      }

      if (term.nominal_voltage) {
        sections.push(`**Nominal Voltage**: ${term.nominal_voltage}`);
      }

      if (term.voltage) {
        sections.push(`**Voltage**: ${term.voltage}`);
      }

      if (term.voltage_ratio) {
        sections.push(`**Voltage Ratio**: ${term.voltage_ratio}`);
      }

      if (term.typical_capacity) {
        sections.push(`**Typical Capacity**: ${term.typical_capacity}`);
      }

      if (term.horizon) {
        sections.push(`**Horizon**: ${term.horizon}`);
      }

      if (term.update_frequency) {
        sections.push(`**Update Frequency**: ${term.update_frequency}`);
      }

      if (term.use_case) {
        sections.push(`**Use Case**: ${term.use_case}`);
      }

      if (term.impact) {
        sections.push(`**Impact**: ${term.impact}`);
      }

      if (term.data_column && term.data_column.length > 0) {
        sections.push(`**Data Columns**: ${term.data_column.join(", ")}`);
      }

      if (term.related && term.related.length > 0) {
        sections.push(`**Related**: ${term.related.join(", ")}`);
      }

      sections.push(""); // Blank line between terms
    }
  }

  return sections.join("\n");
}

/**
 * Create enhanced system prompt with RAG context
 */
export function enhanceSystemPrompt(
  basePrompt: string,
  context: KnowledgeContext,
  language: "en" | "th" = "th"
): string {
  const contextText = formatContext(context, language);

  if (!contextText) {
    return basePrompt;
  }

  // Inject context before guidelines section
  const separator = language === "th" ? "## แนวทางการตอบ" : "## Guidelines";

  if (basePrompt.includes(separator)) {
    return basePrompt.replace(separator, `${contextText}\n\n${separator}`);
  }

  // Fallback: append at the end
  return `${basePrompt}\n\n${contextText}`;
}
