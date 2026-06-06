<script setup lang="ts">
import { computed } from "vue";

import { insightItemTypeLabel, type InsightItem, type InsightRead } from "../types/insight";
import { formatCueTime } from "../types/subtitle";
import { buildTermHighlightSegments, uniqueTermNames } from "../utils/termHighlight";

const props = defineProps<{
  insight: InsightRead | null;
  isLoading: boolean;
  canGenerate: boolean;
}>();

defineEmits<{
  generate: [];
  "select-item": [item: InsightItem];
}>();

const groupedItems = computed(() => {
  if (!props.insight) {
    return [];
  }

  return (["chapter", "key_point", "term", "todo", "decision"] as const)
    .map((type) => ({
      type,
      label: insightItemTypeLabel[type],
      items: props.insight?.items.filter((item) => item.type === type) ?? [],
    }))
    .filter((group) => group.items.length > 0);
});
const termItems = computed(() => props.insight?.items.filter((item) => item.type === "term") ?? []);
const glossaryTerms = computed(() => uniqueTermNames(termItems.value.map((item) => item.title)));
</script>

<template>
  <section class="insight-panel">
    <div class="panel-heading result-heading">
      <div>
        <h2>知识笔记</h2>
        <p class="panel-subtitle">
          {{ insight ? `${insight.items.length} 条洞察` : "从字幕生成结构化笔记" }}
        </p>
      </div>

      <a
        v-if="insight?.markdown_url"
        class="download-link"
        :href="insight.markdown_url"
        download="insight.md"
      >
        下载 MD
      </a>
      <button
        v-else-if="canGenerate"
        class="panel-action-button"
        data-testid="generate-insight"
        type="button"
        :disabled="isLoading"
        @click="$emit('generate')"
      >
        生成知识笔记
      </button>
      <span v-else class="download-disabled">MD 尚未生成</span>
    </div>

    <div v-if="isLoading" class="empty-state">
      正在生成知识笔记
    </div>

    <div v-else-if="!insight" class="empty-state">
      暂无知识笔记
    </div>

    <div v-else class="insight-body">
      <section class="insight-summary">
        <h3>摘要</h3>
        <p>{{ insight.summary }}</p>
      </section>

      <section
        v-if="termItems.length > 0"
        class="video-glossary"
        data-testid="video-glossary"
      >
        <div class="video-glossary-heading">
          <h3>本视频术语表</h3>
          <span>{{ termItems.length }} 个术语</span>
        </div>

        <ol>
          <li
            v-for="item in termItems"
            :key="item.id"
            class="glossary-item"
            role="button"
            tabindex="0"
            @click="$emit('select-item', item)"
            @keydown.enter="$emit('select-item', item)"
          >
            <div class="insight-item-meta">
              <span>{{ formatCueTime(item.start) }} - {{ formatCueTime(item.end) }}</span>
              <span v-if="item.source_cue_indexes.length > 0">
                来源字幕: {{ item.source_cue_indexes.join(", ") }}
              </span>
            </div>
            <strong>{{ item.title }}</strong>
            <p>{{ item.content }}</p>
          </li>
        </ol>
      </section>

      <section
        v-for="group in groupedItems"
        :key="group.type"
        class="insight-group"
      >
        <h3>{{ group.label }}</h3>

        <ol>
          <li
            v-for="item in group.items"
            :key="item.id"
            class="insight-item"
            role="button"
            tabindex="0"
            @click="$emit('select-item', item)"
            @keydown.enter="$emit('select-item', item)"
          >
            <div class="insight-item-meta">
              <span>{{ formatCueTime(item.start) }} - {{ formatCueTime(item.end) }}</span>
              <span v-if="item.source_cue_indexes.length > 0">
                来源字幕: {{ item.source_cue_indexes.join(", ") }}
              </span>
            </div>
            <strong>{{ item.title }}</strong>
            <p>
              <template
                v-for="(segment, segmentIndex) in buildTermHighlightSegments(
                  item.content,
                  glossaryTerms,
                )"
                :key="`${item.id}-${segmentIndex}`"
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
          </li>
        </ol>
      </section>
    </div>
  </section>
</template>
