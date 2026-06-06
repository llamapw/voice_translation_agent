<script setup lang="ts">
import { computed } from "vue";

import { insightItemTypeLabel, type InsightItem, type InsightRead } from "../types/insight";
import { formatCueTime } from "../types/subtitle";

const props = defineProps<{
  insight: InsightRead | null;
  isLoading: boolean;
}>();

defineEmits<{
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
            <p>{{ item.content }}</p>
          </li>
        </ol>
      </section>
    </div>
  </section>
</template>
