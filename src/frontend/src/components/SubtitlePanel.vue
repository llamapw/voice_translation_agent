<script setup lang="ts">
import SubtitleList from "./SubtitleList.vue";
import type { SubtitleCue } from "../types/subtitle";

defineProps<{
  cues: SubtitleCue[];
  srtUrl: string | null;
}>();
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

    <SubtitleList :cues="cues" />
  </section>
</template>
