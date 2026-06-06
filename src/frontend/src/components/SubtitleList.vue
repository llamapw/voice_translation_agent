<script setup lang="ts">
import { formatCueTime, type SubtitleCue } from "../types/subtitle";

defineProps<{
  cues: SubtitleCue[];
  activeCueIndex?: number | null;
}>();

defineEmits<{
  select: [cue: SubtitleCue];
}>();
</script>

<template>
  <div class="subtitle-list">
    <div v-if="cues.length === 0" class="empty-state">
      暂无字幕
    </div>

    <ol v-else>
      <li
        v-for="cue in cues"
        :key="cue.index"
        class="subtitle-item"
        :data-active="cue.index === activeCueIndex"
        role="button"
        tabindex="0"
        @click="$emit('select', cue)"
        @keydown.enter="$emit('select', cue)"
      >
        <div class="cue-meta">
          <strong>#{{ cue.index }}</strong>
          <span>{{ formatCueTime(cue.start) }} - {{ formatCueTime(cue.end) }}</span>
        </div>
        <p class="cue-source">{{ cue.source_text }}</p>
        <p class="cue-target">{{ cue.target_text }}</p>
      </li>
    </ol>
  </div>
</template>
