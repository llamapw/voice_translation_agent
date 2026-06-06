import { describe, expect, it } from "vitest";

import { insightItemTypeLabel, type InsightRead } from "./insight";

describe("insight types helpers", () => {
  it("models single-video insight summaries and timestamped items", () => {
    const insight: InsightRead = {
      job_id: "job_test",
      summary: "运动会产生热量。",
      items: [
        {
          id: "key_point_1",
          type: "key_point",
          title: "片段 1",
          content: "运动会产生热量。",
          start: 0.55,
          end: 13.51,
          source_cue_indexes: [1],
        },
      ],
      markdown_url: "/api/jobs/job_test/insights/markdown",
    };

    expect(insight.items[0].type).toBe("key_point");
    expect(insight.markdown_url).toBe("/api/jobs/job_test/insights/markdown");
  });

  it("maps insight item types to readable labels", () => {
    expect(insightItemTypeLabel.key_point).toBe("关键要点");
    expect(insightItemTypeLabel.term).toBe("术语");
    expect(insightItemTypeLabel.decision).toBe("关键决策");
  });
});
