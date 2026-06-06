<script setup lang="ts">
defineProps<{
  videoUrl: string | null;
  title: string | null;
}>();
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

    <video v-else controls preload="metadata" :src="videoUrl">
      当前浏览器不支持视频播放。
    </video>
  </section>
</template>
