<script setup lang="ts">
import { computed } from "vue";

import SubtitleList from "./SubtitleList.vue";
import { formatCueTime, type SubtitleCue } from "../types/subtitle";

const props = defineProps<{
  cues: SubtitleCue[];
  srtUrl: string | null;
  activeCueIndex?: number | null;
}>();

defineEmits<{
  select: [cue: SubtitleCue];
}>();

const activeCue = computed(
  () => props.cues.find((cue) => cue.index === props.activeCueIndex) ?? null,
);
const timelineEnd = computed(() => Math.max(0, ...props.cues.map((cue) => cue.end)));
</script>

<template>
  <section class="subtitle-panel">
    <div class="panel-heading result-heading">
      <div>
        <h2>字幕结果</h2>
        <p class="panel-subtitle">{{ cues.length }} 条字幕</p>
      </div>

      <a v-if="srtUrl" class="download-link" :href="srtUrl" download="output.srt">
        下载 SRT
      </a>
      <span v-else class="download-disabled">SRT 尚未生成</span>
    </div>

    <div
      v-if="cues.length > 0"
      class="subtitle-timeline-summary"
      data-testid="subtitle-timeline-summary"
    >
      <span>{{ cues.length }} 条字幕</span>
      <span>到 {{ formatCueTime(timelineEnd) }}</span>
      <strong>{{ activeCue ? `当前 #${activeCue.index}` : "等待播放定位" }}</strong>
    </div>

    <SubtitleList
      :cues="cues"
      :active-cue-index="activeCueIndex"
      @select="$emit('select', $event)"
    />
  </section>
</template>
