/**
 * RAG System - Formatter Tests
 */

import { describe, expect, it } from "vitest";
import { enhanceSystemPrompt, formatContext } from "./formatter";
import type { KnowledgeContext } from "./types";

describe("RAG Formatter", () => {
  describe("formatContext", () => {
    it("should format empty context", () => {
      const context: KnowledgeContext = {
        terms: [],
        acronyms: [],
      };

      const formatted = formatContext(context);
      expect(formatted).toBe("");
    });

    it("should format acronyms in Thai", () => {
      const context: KnowledgeContext = {
        terms: [],
        acronyms: [
          { key: "PEA", value: "Provincial Electricity Authority" },
          { key: "MAPE", value: "Mean Absolute Percentage Error" },
        ],
      };

      const formatted = formatContext(context, "th");

      expect(formatted).toContain("## ความรู้ที่เกี่ยวข้อง");
      expect(formatted).toContain("### ตัวย่อ");
      expect(formatted).toContain("**PEA**");
      expect(formatted).toContain("Provincial Electricity Authority");
    });

    it("should format terms in English", () => {
      const context: KnowledgeContext = {
        terms: [
          {
            key: "mape",
            term: {
              en: "Mean Absolute Percentage Error",
              th: "ค่าความคลาดเคลื่อนสัมบูรณ์เฉลี่ยร้อยละ",
              definition: "Accuracy metric for forecasts",
              target: "< 10%",
              formula: "mean(|actual - predicted| / actual) × 100",
            },
            relevance: 10,
          },
        ],
        acronyms: [],
      };

      const formatted = formatContext(context, "en");

      expect(formatted).toContain("## Relevant Knowledge");
      expect(formatted).toContain("### Technical Terms");
      expect(formatted).toContain("Mean Absolute Percentage Error");
      expect(formatted).toContain("**Definition**: Accuracy metric");
      expect(formatted).toContain("**Target**: < 10%");
      expect(formatted).toContain("**Formula**:");
    });

    it("should include all metadata fields", () => {
      const context: KnowledgeContext = {
        terms: [
          {
            key: "voltage_limit",
            term: {
              en: "Voltage Limit",
              th: "ขีดจำกัดแรงดัน",
              definition: "Acceptable voltage range",
              nominal: "230V",
              upper_limit: "242V (+5%)",
              lower_limit: "218V (-5%)",
              related: ["overvoltage", "undervoltage"],
            },
            relevance: 8,
          },
        ],
        acronyms: [],
      };

      const formatted = formatContext(context, "en");

      expect(formatted).toContain("**Nominal**: 230V");
      expect(formatted).toContain("**Upper Limit**: 242V");
      expect(formatted).toContain("**Lower Limit**: 218V");
      expect(formatted).toContain("**Related**: overvoltage, undervoltage");
    });

    it("should format multiple terms", () => {
      const context: KnowledgeContext = {
        terms: [
          {
            key: "irradiance",
            term: {
              en: "Solar Irradiance",
              th: "ความเข้มแสงอาทิตย์",
              definition: "Power per unit area from the Sun",
              unit: "W/m²",
            },
            relevance: 9,
          },
          {
            key: "prosumer",
            term: {
              en: "Prosumer",
              th: "โปรซูเมอร์",
              definition: "Consumer who also produces electricity",
            },
            relevance: 7,
          },
        ],
        acronyms: [],
      };

      const formatted = formatContext(context, "th");

      expect(formatted).toContain("Solar Irradiance");
      expect(formatted).toContain("Prosumer");
      expect(formatted).toContain("**Unit**: W/m²");
    });
  });

  describe("enhanceSystemPrompt", () => {
    it("should inject context before guidelines (Thai)", () => {
      const basePrompt = `คุณเป็นผู้ช่วย AI

## แนวทางการตอบ
- ให้ข้อมูลที่เป็นประโยชน์`;

      const context: KnowledgeContext = {
        terms: [
          {
            key: "mape",
            term: {
              en: "MAPE",
              th: "เมป",
              definition: "Accuracy metric",
            },
            relevance: 10,
          },
        ],
        acronyms: [],
      };

      const enhanced = enhanceSystemPrompt(basePrompt, context, "th");

      expect(enhanced).toContain("## ความรู้ที่เกี่ยวข้อง");
      expect(enhanced).toContain("## แนวทางการตอบ");
      // Context should come before guidelines
      expect(enhanced.indexOf("ความรู้")).toBeLessThan(enhanced.indexOf("แนวทางการตอบ"));
    });

    it("should inject context before guidelines (English)", () => {
      const basePrompt = `You are an AI assistant

## Guidelines
- Be helpful`;

      const context: KnowledgeContext = {
        terms: [
          {
            key: "prosumer",
            term: {
              en: "Prosumer",
              th: "โปรซูเมอร์",
              definition: "Producer + Consumer",
            },
            relevance: 8,
          },
        ],
        acronyms: [],
      };

      const enhanced = enhanceSystemPrompt(basePrompt, context, "en");

      expect(enhanced).toContain("## Relevant Knowledge");
      expect(enhanced).toContain("## Guidelines");
      expect(enhanced.indexOf("Relevant Knowledge")).toBeLessThan(enhanced.indexOf("Guidelines"));
    });

    it("should append context if no guidelines section found", () => {
      const basePrompt = "You are a helpful assistant.";

      const context: KnowledgeContext = {
        terms: [],
        acronyms: [{ key: "PEA", value: "Provincial Electricity Authority" }],
      };

      const enhanced = enhanceSystemPrompt(basePrompt, context, "en");

      expect(enhanced).toContain("You are a helpful assistant.");
      expect(enhanced).toContain("## Relevant Knowledge");
      expect(enhanced).toContain("PEA");
    });

    it("should not modify prompt if context is empty", () => {
      const basePrompt = "You are a helpful assistant.";
      const context: KnowledgeContext = {
        terms: [],
        acronyms: [],
      };

      const enhanced = enhanceSystemPrompt(basePrompt, context);

      expect(enhanced).toBe(basePrompt);
    });
  });
});
