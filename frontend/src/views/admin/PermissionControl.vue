<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Lock, RefreshRight, Setting, UserFilled } from '@element-plus/icons-vue'

import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import {
  fetchAdminPermissionSettings,
  updateAdminPermissionSettings,
} from '../../api/admin'

const loading = ref(false)
const modules = ref([])

const stats = computed(() => {
  const total = modules.value.length
  const editable = modules.value.filter((item) => item.edit).length
  const approvable = modules.value.filter((item) => item.approve).length
  const exportable = modules.value.filter((item) => item.export).length

  return [
    { label: '权限模块', value: total, suffix: ' 项', tone: 'primary', icon: Lock },
    { label: '可编辑模块', value: editable, suffix: ' 项', tone: 'success', icon: Setting },
    { label: '可审批模块', value: approvable, suffix: ' 项', tone: 'warning', icon: UserFilled },
    { label: '可导出模块', value: exportable, suffix: ' 项', tone: 'info', icon: RefreshRight },
  ]
})

const loadData = async () => {
  loading.value = true
  try {
    const { data } = await fetchAdminPermissionSettings()
    modules.value = (data.data?.modules || []).map((item) => ({ ...item }))
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.response?.data?.message || error?.response?.data?.detail || '权限配置加载失败')
  } finally {
    loading.value = false
  }
}

const save = async () => {
  loading.value = true
  try {
    await updateAdminPermissionSettings({ modules: modules.value })
    ElMessage.success('权限配置已保存')
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.response?.data?.message || error?.response?.data?.detail || '权限配置保存失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div class="page-shell permission-page">
    <PageSectionHeader
      eyebrow="系统配置"
      title="权限控制"
      description="配置平台管理员各业务模块的查看、编辑、审批和导出权限。"
      chip="权限矩阵"
    >
      <template #actions>
        <el-button :icon="RefreshRight" :loading="loading" @click="loadData">刷新</el-button>
      </template>
    </PageSectionHeader>

    <section class="stats-grid stats-grid--permissions">
      <MetricCard
        v-for="item in stats"
        :key="item.label"
        :label="item.label"
        :value="item.value"
        :suffix="item.suffix"
        :tone="item.tone"
        :icon="item.icon"
      />
    </section>

    <section class="page-panel surface-card">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">模块权限</h3>
          <p class="panel-heading__desc">按模块维护后台操作权限，保存后即时生效。</p>
        </div>
        <div class="toolbar-actions">
          <el-button type="primary" :loading="loading" @click="save">保存配置</el-button>
        </div>
      </div>

      <el-table :data="modules" v-loading="loading" stripe>
        <el-table-column prop="module" label="模块名称" min-width="220" />
        <el-table-column label="查看权限" width="140" align="center">
          <template #default="{ row }">
            <el-switch v-model="row.view" />
          </template>
        </el-table-column>
        <el-table-column label="编辑权限" width="140" align="center">
          <template #default="{ row }">
            <el-switch v-model="row.edit" />
          </template>
        </el-table-column>
        <el-table-column label="审批权限" width="140" align="center">
          <template #default="{ row }">
            <el-switch v-model="row.approve" />
          </template>
        </el-table-column>
        <el-table-column label="导出权限" width="140" align="center">
          <template #default="{ row }">
            <el-switch v-model="row.export" />
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>
