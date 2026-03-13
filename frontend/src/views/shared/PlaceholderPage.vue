<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const title = computed(() => route.meta.title || '功能开发中')
</script>

<template>
  <div class="placeholder-root">
    <el-empty
      :description="`${title}：功能开发中，稍后提供完整界面`"
    />
  </div>
</template>

<style scoped>
.placeholder-root {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>

