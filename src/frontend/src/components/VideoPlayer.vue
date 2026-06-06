<script setup lang="ts">
import { computed, ref } from "vue";

import { formatCueTime } from "../types/subtitle";

defineProps<{
  videoUrl: string | null;
  title: string | null;
}>();

const emit = defineEmits<{
  timeupdate: [currentTime: number];
}>();

const videoElement = ref<HTMLVideoElement | null>(null);
const currentTime = ref(0);
const duration = ref<number | null>(null);

const timeDisplay = computed(() => {
  const durationLabel = duration.value === null ? "--:--.---" : formatCueTime(duration.value);

  return `${formatCueTime(currentTime.value)} / ${durationLabel}`;
});

function handleLoadedMetadata(): void {
  if (videoElement.value !== null && Number.isFinite(videoElement.value.duration)) {
    duration.value = videoElement.value.duration;
  }
}

function handleTimeUpdate(): void {
  if (videoElement.value !== null) {
    currentTime.value = videoElement.value.currentTime;
    emit("timeupdate", currentTime.value);
  }
}

function seekTo(seconds: number): void {
  if (videoElement.value !== null) {
    videoElement.value.currentTime = seconds;
    currentTime.value = seconds;
  }
}

defineExpose({
  seekTo,
});
</script>

<template>
  <section class="video-panel">
    <div class="panel-heading">
      <h2>视频预览</h2>
      <p v-if="title" class="panel-subtitle">{{ title }}</p>
    </div>

    <div v-if="!videoUrl" class="empty-state">
      等待视频生成
    </div>

    <video
      v-else
      ref="videoElement"
      controls
      preload="metadata"
      :src="videoUrl"
      @loadedmetadata="handleLoadedMetadata"
      @timeupdate="handleTimeUpdate"
    >
      当前浏览器不支持视频播放。
    </video>
    <div v-if="videoUrl" class="video-time-display" data-testid="video-time-display">
      {{ timeDisplay }}
    </div>
  </section>
</template>
