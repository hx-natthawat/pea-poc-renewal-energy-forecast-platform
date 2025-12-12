/**
 * RAG System - Search Tests
 */

import { beforeEach, describe, expect, it } from "vitest";
import { clearGlossaryCache } from "./loader";
import { extractKeywords, searchKnowledge } from "./search";

describe("RAG Search System", () => {
  beforeEach(() => {
    clearGlossaryCache();
  });

  describe("extractKeywords", () => {
    it("should extract keywords from English query", () => {
      const keywords = extractKeywords("What is MAPE and RMSE?");
      expect(keywords).toContain("mape");
      expect(keywords).toContain("rmse");
    });

    it("should extract keywords from Thai query", () => {
      const keywords = extractKeywords("แรงดัน เกิน คือ อะไร");
      expect(keywords).toContain("แรงดัน");
      expect(keywords).toContain("เกิน");
    });

    it("should filter out common words", () => {
      const keywords = extractKeywords("What is the voltage limit?");
      expect(keywords).not.toContain("what");
      expect(keywords).not.toContain("the");
      expect(keywords).toContain("voltage");
      expect(keywords).toContain("limit");
    });

    it("should handle mixed English and Thai", () => {
      const keywords = extractKeywords("MAPE คืออะไร");
      expect(keywords).toContain("mape");
    });
  });

  describe("searchKnowledge", () => {
    it("should find MAPE term", () => {
      const context = searchKnowledge("What is MAPE?");

      expect(context.terms.length).toBeGreaterThan(0);
      const mapeTerm = context.terms.find((t) => t.key === "mape");
      expect(mapeTerm).toBeDefined();
      expect(mapeTerm?.term.en).toBe("Mean Absolute Percentage Error");
    });

    it("should find voltage-related terms", () => {
      const context = searchKnowledge("voltage limit overvoltage");

      expect(context.terms.length).toBeGreaterThan(0);
      const hasVoltageTerms = context.terms.some(
        (t) => t.key === "voltage_limit" || t.key === "overvoltage" || t.key === "undervoltage"
      );
      expect(hasVoltageTerms).toBe(true);
    });

    it("should find prosumer term with Thai query", () => {
      const context = searchKnowledge("โปรซูเมอร์คืออะไร");

      const prosumerTerm = context.terms.find((t) => t.key === "prosumer");
      expect(prosumerTerm).toBeDefined();
    });

    it("should find acronyms", () => {
      const context = searchKnowledge("What is PEA?");

      expect(context.acronyms.length).toBeGreaterThan(0);
      const peaAcronym = context.acronyms.find((a) => a.key === "PEA");
      expect(peaAcronym).toBeDefined();
      expect(peaAcronym?.value).toContain("Provincial Electricity Authority");
    });

    it("should include related terms when configured", () => {
      const context = searchKnowledge("irradiance", {
        maxResults: 3,
        includeRelated: true,
      });

      const irradianceTerm = context.terms.find((t) => t.key === "irradiance");
      expect(irradianceTerm).toBeDefined();

      // Should include related terms like pyranometer
      const relatedKeys = context.terms.map((t) => t.key);
      expect(relatedKeys.length).toBeGreaterThan(1);
    });

    it("should respect maxResults config", () => {
      const context = searchKnowledge("voltage power energy", {
        maxResults: 2,
        includeRelated: false,
      });

      expect(context.terms.length).toBeLessThanOrEqual(2);
    });

    it("should respect minRelevance config", () => {
      const context = searchKnowledge("test query with no matches", {
        minRelevance: 10, // Very high threshold
      });

      expect(context.terms.length).toBe(0);
    });

    it("should handle empty query gracefully", () => {
      const context = searchKnowledge("");

      expect(context.terms).toEqual([]);
      expect(context.acronyms).toEqual([]);
    });

    it("should rank exact matches higher", () => {
      const context = searchKnowledge("mape");

      expect(context.terms.length).toBeGreaterThan(0);
      // MAPE should be the first result due to exact match
      expect(context.terms[0].key).toBe("mape");
      expect(context.terms[0].relevance).toBeGreaterThan(5);
    });

    it("should find terms by data column name", () => {
      const context = searchKnowledge("pvtemp1");

      const pvTempTerm = context.terms.find((t) => t.key === "pv_temperature");
      expect(pvTempTerm).toBeDefined();
    });

    it("should handle complex multi-term queries", () => {
      const context = searchKnowledge("How does solar irradiance affect power output?");

      const termKeys = context.terms.map((t) => t.key);
      expect(termKeys).toContain("irradiance");
      expect(termKeys).toContain("power_output");
    });
  });
});
