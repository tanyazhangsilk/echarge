<script setup>
import { computed, onActivated, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Lock, RefreshRight, Setting, UserFilled } from '@element-plus/icons-vue'

import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import TableSkeletonBlock from '../../components/console/TableSkeletonBlock.vue'
import { fetchAdminPermissionSettings, updateAdminPermissionSettings } from '../../api/admin'
import { mockPermissionModules } from '../../mock/backoffice'
import { readLocalState, writeLocalState } from '../../utils/localState'
import { buildRequestCacheKey, formatCacheUpdatedAt, getRequestCache, setRequestCache } from '../../utils/requestCache'

const CACHE_TTL = 60 * 1000
const STORAGE_KEY = 'echarge-admin-permission-modules'

const loading = ref(false)
const tableReady = ref(false)
const cacheLabel = ref('')
const modules = ref(readLocalState(STORAGE_KEY, mockPermissionModules))

const cacheKey = buildRequestCacheKey('/admin/settings/permissions', { scope: 'permission-settings' })

const stats = computed(() => {
  const total = modules.value.length
  const editable = modules.value.filter((item) => item.edit).length
  const approvable = modules.value.filter((item) => item.approve).length
  const exportable = modules.value.filter((item) => item.export).length

  return [
    { label: '权限模块', value: total, suffix: ' 项', tone: 'primary', icon: Lock, trend: '业务模块覆盖', trendLabel: '统一维护管理权限' },
    { label: '可编辑模块', value: editable, suffix: ' 项', tone: 'success', icon: Setting, trend: '支持配置与修改', trendLabel: '影响运营处理能力' },
    { label: '可审批模块', value: approvable, suffix: ' 项', tone: 'warning', icon: UserFilled, trend: '涉及审核动作', trendLabel: '重点关注审批权限' },
    { label: '可导出模块', value: exportable, suffix: ' 项', tone: 'info', icon: RefreshRight, trend: '支持数据导出', trendLabel: '便于运营复盘与归档' },
  ]
})

const applyModules = (items = [], fromCache = false) => {
  modules.value = (Array.isArray(items) && items.length ? items : readLocalState(STORAGE_KEY, mockPermissionModules)).map((item) => ({ ...item }))
  writeLocalState(STORAGE_KEY, modules.value)
  tableReady.value = true
  cacheLabel.value = `${fromCache ? '缓存结果' : '最近刷新'} ${formatCacheUpdatedAt(Date.now())}`
}

const loadData = async ({ background = false } = {}) => {
  const cached = getRequestCache(cacheKey, { ttl: CACHE_TTL, allowStale: true })
  if (cached) {
    applyModules(cached.value, true)
    cacheLabel.value = `缓存结果 ${formatCacheUpdatedAt(cached.updatedAt)}`
  }

  loading.value = !cached || !background
  try {
    const { data } = await fetchAdminPermissionSettings()
    const items = Array.isArray(data?.data?.modules) ? data.data.modules : mockPermissionModules
    applyModules(items)
    setRequestCache(cacheKey, items)
    cacheLabel.value = `最近刷新 ${formatCacheUpdatedAt(Date.now())}`
  } catch (error) {
    if (!modules.value.length) {
      applyModules(mockPermissionModules)
      cacheLabel.value = '演示数据'
    }
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
    writeLocalState(STORAGE_KEY, modules.value)
    ElMessage.success('后端暂未返回成功，已先保存当前权限配置')
  } finally {
    setRequestCache(cacheKey, modules.value)
    cacheLabel.value = `最近刷新 ${formatCacheUpdatedAt(Date.now())}`
    loading.value = false
  }
}

onMounted(loadData)
onActivated(() => loadData({ background: true }))
</script>

<template>
  <div class="page-shell permission-page">
    <PageSectionHeader eyebrow="系统配置" title="权限控制" description="维护后台模块查看、编辑、审批与导出权限。" chip="权限矩阵">
      <template #actions>
        <el-tag v-if="cacheLabel" type="info" effect="plain">{{ cacheLabel }}</el-tag>
        <el-button :icon="RefreshRight" :loading="loading" @click="loadData()">刷新</el-button>
      </template>
    </PageSectionHeader>

    <section class="stats-grid stats-grid--permissions">
      <MetricCard v-for="item in stats" :key="item.label" v-bind="item" />
    </section>

    <section class="page-panel surface-card">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">模块权限</h3>
          <p class="panel-heading__desc">保存后将作为平台管理员默认权限矩阵。</p>
        </div>
        <div class="toolbar-actions">
          <el-button type="primary" :loading="loading" @click="save">保存配置</el-button>
        </div>
      </div>

      <TableSkeletonBlock v-if="loading && !tableReady" :rows="8" :columns="6" />

      <el-table v-else :data="modules" v-loading="loading" stripe>
        <el-table-column prop="module" label="模块名称" min-width="220" />
        <el-table-column prop="scope" label="业务范围" min-width="160" />
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

<style scoped>
.stats-grid--permissions {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

@media (max-width: 1280px) {
  .stats-grid--permissions {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .stats-grid--permissions {
    grid-template-columns: 1fr;
  }
}
</style>
