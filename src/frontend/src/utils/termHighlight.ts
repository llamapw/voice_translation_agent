import type { InsightItem } from "../types/insight";

export interface TermHighlightSegment {
  text: string;
  highlighted: boolean;
}

export function uniqueTermNames(terms: string[]): string[] {
  const seen = new Set<string>();
  const names: string[] = [];

  for (const term of terms) {
    const trimmed = term.trim();
    const key = trimmed.toLocaleLowerCase();
    if (!trimmed || seen.has(key)) {
      continue;
    }

    seen.add(key);
    names.push(trimmed);
  }

  return names;
}

export function buildInsightTermNames(items: InsightItem[]): string[] {
  return uniqueTermNames(
    items
      .filter((item) => item.type === "term")
      .flatMap((item) => [item.source_term ?? "", item.target_term ?? "", item.title]),
  );
}

export function buildTermHighlightSegments(
  text: string,
  terms: string[],
): TermHighlightSegment[] {
  const normalizedTerms = uniqueTermNames(terms).sort((left, right) => right.length - left.length);

  if (!text || normalizedTerms.length === 0) {
    return [{ text, highlighted: false }];
  }

  const segments: TermHighlightSegment[] = [];
  const lowerText = text.toLocaleLowerCase();
  let cursor = 0;

  while (cursor < text.length) {
    const matchedTerm = normalizedTerms.find((term) =>
      lowerText.startsWith(term.toLocaleLowerCase(), cursor),
    );

    if (!matchedTerm) {
      const nextMatchIndex = findNextMatchIndex(lowerText, normalizedTerms, cursor + 1);
      const end = nextMatchIndex >= 0 ? nextMatchIndex : text.length;
      segments.push({ text: text.slice(cursor, end), highlighted: false });
      cursor = end;
      continue;
    }

    segments.push({
      text: text.slice(cursor, cursor + matchedTerm.length),
      highlighted: true,
    });
    cursor += matchedTerm.length;
  }

  return segments;
}

function findNextMatchIndex(lowerText: string, terms: string[], start: number): number {
  const matches = terms
    .map((term) => lowerText.indexOf(term.toLocaleLowerCase(), start))
    .filter((index) => index >= 0);

  return matches.length > 0 ? Math.min(...matches) : -1;
}
