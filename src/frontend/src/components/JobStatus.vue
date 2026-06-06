<script setup lang="ts">
import { computed } from "vue";

import { statusLabel, type JobRead } from "../types/job";

const props = defineProps<{
  job: JobRead | null;
}>();

const progressValue = computed(() => {
  if (!props.job) {
    return 0;
  }

  return Math.min(100, Math.max(0, props.job.progress));
});
</script>

<template>
  <section class="job-status-panel">
    <div class="panel-heading">
      <h2>任务状态</h2>
    </div>

    <div v-if="!job" class="empty-state">
      等待上传任务
    </div>

    <div v-else class="job-status-body">
      <div class="status-row">
        <span class="status-pill" :data-status="job.status">{{ statusLabel[job.status] }}</span>
        <span class="job-id">{{ job.id }}</span>
      </div>

      <dl class="job-config-summary" data-testid="job-config-summary">
        <div>
          <dt>语言</dt>
          <dd>{{ job.source_language }} → {{ job.target_language }}</dd>
        </div>
        <div>
          <dt>字幕</dt>
          <dd>{{ job.subtitle_mode }}</dd>
        </div>
        <div>
          <dt>模型</dt>
          <dd>{{ job.asr_model }}</dd>
        </div>
      </dl>

      <div class="progress-block">
        <div class="progress-meta">
          <span>{{ job.message }}</span>
          <strong>{{ progressValue }}%</strong>
        </div>
        <div class="progress-track">
          <div
            data-testid="job-progress"
            class="progress-fill"
            :style="{ width: `${progressValue}%` }"
          />
        </div>
      </div>

      <p v-if="job.error" class="error-message">{{ job.error }}</p>
    </div>
  </section>
</template>
