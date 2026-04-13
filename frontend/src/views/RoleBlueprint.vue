<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goSettings = () => {
  router.push('/admin/settings')
}
</script>

<template>
  <div class="page-shell">
    <el-result
      icon="info"
      title="页面已迁移"
      sub-title="请前往系统设置页面维护平台参数。"
    >
      <template #extra>
        <el-button type="primary" @click="goSettings">进入系统设置</el-button>
      </template>
    </el-result>
  </div>
</template>
