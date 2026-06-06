export type InsightItemType = "key_point" | "chapter" | "term" | "todo" | "decision";

export interface InsightItem {
  id: string;
  type: InsightItemType;
  title: string;
  content: string;
  start: number;
  end: number;
  source_cue_indexes: number[];
}

export interface InsightRead {
  job_id: string;
  summary: string;
  items: InsightItem[];
  markdown_url: string | null;
}

export const insightItemTypeLabel: Record<InsightItemType, string> = {
  chapter: "章节",
  key_point: "关键要点",
  term: "术语",
  todo: "待办",
  decision: "关键决策",
};
