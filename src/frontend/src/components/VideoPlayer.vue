<script setup lang="ts">
import { ref } from "vue";

defineProps<{
  videoUrl: string | null;
  title: string | null;
}>();

const emit = defineEmits<{
  timeupdate: [currentTime: number];
}>();

const videoElement = ref<HTMLVideoElement | null>(null);

function handleTimeUpdate(): void {
  if (videoElement.value !== null) {
    emit("timeupdate", videoElement.value.currentTime);
  }
}

function seekTo(seconds: number): void {
  if (videoElement.value !== null) {
    videoElement.value.currentTime = seconds;
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
      @timeupdate="handleTimeUpdate"
    >
      当前浏览器不支持视频播放。
    </video>
  </section>
</template>
