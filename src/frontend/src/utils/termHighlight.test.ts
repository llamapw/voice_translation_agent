import { describe, expect, it } from "vitest";

import type { InsightItem } from "../types/insight";
import { buildInsightTermNames, buildTermHighlightSegments, uniqueTermNames } from "./termHighlight";

describe("termHighlight", () => {
  it("builds text segments for matched terms without using html strings", () => {
    expect(buildTermHighlightSegments("热应激会导致核心温度升高", ["热应激"])).toEqual([
      { text: "热应激", highlighted: true },
      { text: "会导致核心温度升高", highlighted: false },
    ]);
  });

  it("prefers the longest term when terms overlap", () => {
    expect(buildTermHighlightSegments("可补偿热应激", ["热应激", "可补偿热应激"])).toEqual([
      { text: "可补偿热应激", highlighted: true },
    ]);
  });

  it("deduplicates empty and repeated term names", () => {
    expect(uniqueTermNames([" 热应激 ", "", "热应激", "Core Temperature"])).toEqual([
      "热应激",
      "Core Temperature",
    ]);
  });

  it("builds highlight names from bilingual term insight fields", () => {
    const items: InsightItem[] = [
      {
        id: "term_1",
        type: "term",
        title: "热应激",
        content: "身体热量压力相关概念。",
        start: 0.55,
        end: 13.51,
        source_cue_indexes: [1],
        source_term: "heat stress",
        target_term: "热应激",
      },
    ];

    expect(buildInsightTermNames(items)).toEqual(["heat stress", "热应激"]);
  });
});
