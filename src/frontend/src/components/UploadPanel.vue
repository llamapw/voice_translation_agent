<script setup lang="ts">
import { computed, ref } from "vue";

import type { CreateJobInput } from "../api/jobs";
import type { SubtitleMode } from "../types/job";

const props = withDefaults(
  defineProps<{
    isSubmitting?: boolean;
  }>(),
  {
    isSubmitting: false,
  },
);

const emit = defineEmits<{
  submit: [payload: CreateJobInput];
}>();

const selectedFile = ref<File | null>(null);
const sourceLanguage = ref("zh");
const targetLanguage = ref("zh");
const correctText = ref(true);
const subtitleMode = ref<SubtitleMode>("bilingual");

const canSubmit = computed(() => selectedFile.value !== null && !props.isSubmitting);

function handleFileChange(event: Event): void {
  const input = event.target as HTMLInputElement;
  selectedFile.value = input.files?.[0] ?? null;
}

function submitUpload(): void {
  if (!selectedFile.value || props.isSubmitting) {
    return;
  }

  emit("submit", {
    file: selectedFile.value,
    source_language: sourceLanguage.value,
    target_language: targetLanguage.value,
    correct: correctText.value,
    asr_model: "paraformer-v2",
    llm_model: "default",
    subtitle_mode: subtitleMode.value,
  });
}
</script>

<template>
  <form class="upload-panel" @submit.prevent="submitUpload">
    <div class="panel-heading">
      <h2>上传视频</h2>
    </div>

    <label class="field">
      <span>视频文件</span>
      <input
        data-testid="video-file"
        type="file"
        accept="video/*,.mp4,.mov,.mkv,.avi"
        :disabled="props.isSubmitting"
        @change="handleFileChange"
      />
    </label>

    <div class="field-grid">
      <label class="field">
        <span>源语言</span>
        <select
          v-model="sourceLanguage"
          data-testid="source-language"
          :disabled="props.isSubmitting"
        >
          <option value="zh">中文</option>
          <option value="en">English</option>
          <option value="ja">日本語</option>
          <option value="ko">한국어</option>
        </select>
      </label>

      <label class="field">
        <span>目标语言</span>
        <select
          v-model="targetLanguage"
          data-testid="target-language"
          :disabled="props.isSubmitting"
        >
          <option value="zh">中文</option>
          <option value="en">English</option>
          <option value="ja">日本語</option>
          <option value="ko">한국어</option>
        </select>
      </label>
    </div>

    <label class="field">
      <span>字幕模式</span>
      <select
        v-model="subtitleMode"
        data-testid="subtitle-mode"
        :disabled="props.isSubmitting"
      >
        <option value="source">原文字幕</option>
        <option value="target">译文字幕</option>
        <option value="bilingual">双语字幕</option>
      </select>
    </label>

    <label class="check-field">
      <input
        v-model="correctText"
        data-testid="correct-text"
        type="checkbox"
        :disabled="props.isSubmitting"
      />
      <span>启用文本修正</span>
    </label>

    <button data-testid="submit-upload" type="submit" :disabled="!canSubmit">
      {{ props.isSubmitting ? "上传中..." : "开始生成字幕" }}
    </button>
  </form>
</template>
