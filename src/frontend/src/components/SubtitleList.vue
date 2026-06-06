<script setup lang="ts">
import type { ComponentPublicInstance } from "vue";
import { nextTick, ref, watch } from "vue";

import { formatCueTime, type SubtitleCue } from "../types/subtitle";
import { buildTermHighlightSegments } from "../utils/termHighlight";

const props = withDefaults(defineProps<{
  cues: SubtitleCue[];
  activeCueIndex?: number | null;
  terms?: string[];
}>(), {
  terms: () => [],
});

defineEmits<{
  select: [cue: SubtitleCue];
}>();

const cueItemRefs = new Map<number, HTMLElement>();
const subtitleListElement = ref<HTMLElement | null>(null);

function formatCueDuration(cue: SubtitleCue): string {
  return `${Math.max(0, cue.end - cue.start).toFixed(2)}s`;
}

function setCueItemRef(
  cueIndex: number,
  element: Element | ComponentPublicInstance | null,
): void {
  if (element instanceof HTMLElement) {
    cueItemRefs.set(cueIndex, element);
    return;
  }

  cueItemRefs.delete(cueIndex);
}

function scrollActiveCueIntoView(activeCueIndex: number | null | undefined): void {
  if (activeCueIndex === null || activeCueIndex === undefined) {
    return;
  }

  const scrollContainer = subtitleListElement.value;
  const activeCue = cueItemRefs.get(activeCueIndex);
  if (!scrollContainer || !activeCue) {
    return;
  }

  const targetScrollTop =
    activeCue.offsetTop - scrollContainer.clientHeight / 2 + activeCue.clientHeight / 2;
  const top = Math.max(0, targetScrollTop);
  if (typeof scrollContainer.scrollTo === "function") {
    scrollContainer.scrollTo({
      top,
      behavior: "smooth",
    });
    return;
  }

  scrollContainer.scrollTop = top;
}

watch(
  () => props.activeCueIndex,
  async (activeCueIndex) => {
    await nextTick();
    scrollActiveCueIntoView(activeCueIndex);
  },
);
</script>

<template>
  <div ref="subtitleListElement" class="subtitle-list" data-testid="subtitle-list">
    <div v-if="cues.length === 0" class="subtitle-empty-guide" data-testid="subtitle-empty-guide">
      <div class="subtitle-empty-intro">
        <strong>字幕会在这里生成</strong>
        <span>上传视频并启动任务后，可以实时查看字幕列表和时间轴联动结果。</span>
      </div>
      <ol class="subtitle-empty-steps" aria-label="字幕生成流程">
        <li>
          <span>1</span>
          <strong>上传视频</strong>
        </li>
        <li>
          <span>2</span>
          <strong>实时生成字幕</strong>
        </li>
        <li>
          <span>3</span>
          <strong>播放联动与导出</strong>
        </li>
      </ol>
    </div>

    <ol v-else>
      <li
        v-for="cue in cues"
        :key="cue.index"
      >
        <button
          class="subtitle-item"
          type="button"
          :ref="(element) => setCueItemRef(cue.index, element)"
          :data-subtitle-cue-index="cue.index"
          :data-active="cue.index === activeCueIndex"
          :aria-current="cue.index === activeCueIndex ? 'true' : undefined"
          @click="$emit('select', cue)"
        >
          <div class="cue-meta">
            <strong>#{{ cue.index }}</strong>
            <span>{{ formatCueTime(cue.start) }} - {{ formatCueTime(cue.end) }}</span>
          </div>
          <div class="cue-support">
            <span :data-testid="`cue-duration-${cue.index}`">持续 {{ formatCueDuration(cue) }}</span>
            <span v-if="cue.index === activeCueIndex" class="cue-active-label">当前字幕</span>
          </div>
          <p class="cue-source">
            <template
              v-for="(segment, segmentIndex) in buildTermHighlightSegments(cue.source_text, terms)"
              :key="`source-${cue.index}-${segmentIndex}`"
            >
              <mark
                v-if="segment.highlighted"
                class="term-highlight"
                :data-testid="`term-highlight-${segment.text}`"
              >
                {{ segment.text }}
              </mark>
              <template v-else>{{ segment.text }}</template>
            </template>
          </p>
          <p class="cue-target">
            <template
              v-for="(segment, segmentIndex) in buildTermHighlightSegments(cue.target_text, terms)"
              :key="`target-${cue.index}-${segmentIndex}`"
            >
              <mark
                v-if="segment.highlighted"
                class="term-highlight"
                :data-testid="`term-highlight-${segment.text}`"
              >
                {{ segment.text }}
              </mark>
              <template v-else>{{ segment.text }}</template>
            </template>
          </p>
        </button>
      </li>
    </ol>
  </div>
</template>
