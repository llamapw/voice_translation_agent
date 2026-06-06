export interface SubtitleCue {
  index: number;
  start: number;
  end: number;
  source_text: string;
  target_text: string;
  display_text: string | null;
}

export function formatCueTime(seconds: number): string {
  const safeSeconds = Math.max(0, seconds);
  const minutes = Math.floor(safeSeconds / 60);
  const wholeSeconds = Math.floor(safeSeconds % 60);
  const milliseconds = Math.round((safeSeconds - Math.floor(safeSeconds)) * 1000);

  return [
    String(minutes).padStart(2, "0"),
    ":",
    String(wholeSeconds).padStart(2, "0"),
    ".",
    String(milliseconds).padStart(3, "0"),
  ].join("");
}
