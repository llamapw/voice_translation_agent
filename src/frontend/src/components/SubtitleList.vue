<script setup lang="ts">
import { formatCueTime, type SubtitleCue } from "../types/subtitle";

defineProps<{
  cues: SubtitleCue[];
  activeCueIndex?: number | null;
}>();

defineEmits<{
  select: [cue: SubtitleCue];
}>();

function formatCueDuration(cue: SubtitleCue): string {
  return `${Math.max(0, cue.end - cue.start).toFixed(2)}s`;
}
</script>

<template>
  <div class="subtitle-list">
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
        class="subtitle-item"
        :data-active="cue.index === activeCueIndex"
        :aria-current="cue.index === activeCueIndex ? 'true' : undefined"
        role="button"
        tabindex="0"
        @click="$emit('select', cue)"
        @keydown.enter="$emit('select', cue)"
      >
        <div class="cue-meta">
          <strong>#{{ cue.index }}</strong>
          <span>{{ formatCueTime(cue.start) }} - {{ formatCueTime(cue.end) }}</span>
        </div>
        <div class="cue-support">
          <span :data-testid="`cue-duration-${cue.index}`">持续 {{ formatCueDuration(cue) }}</span>
          <span v-if="cue.index === activeCueIndex" class="cue-active-label">当前字幕</span>
        </div>
        <p class="cue-source">{{ cue.source_text }}</p>
        <p class="cue-target">{{ cue.target_text }}</p>
      </li>
    </ol>
  </div>
</template>
