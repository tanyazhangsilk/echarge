<script setup>
import { computed, onActivated, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Lock, RefreshRight, Setting, UserFilled } from '@element-plus/icons-vue'

import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import TableSkeletonBlock from '../../components/console/TableSkeletonBlock.vue'
import { fetchAdminPermissionSettings, updateAdminPermissionSettings } from '../../api/admin'
import { readLocalState, writeLocalState } from '../../utils/localState'
import { buildRequestCacheKey, formatCacheLabel, getRequestCache, setRequestCache, shouldRefreshRequestCache } from '../../utils/requestCache'

const STORAGE_KEY = 'echarge-admin-role-permissions'
const CACHE_TTL = 60 * 1000

const defaultRoles = [
  {
    key: 'platform-admin',
    roleName: '平台管理员',
    scope: '负责全局治理、审核策略和关键配置变更',
    members: 3,
    modules: ['工作台总览', '运营商审核', '电站审核', '全局订单', '异常订单', '平台清分', '发票管理', '系统参数'],
    canEdit: true,
    canApprove: true,
    canExport: true,
    enabled: true,
  },
  {
    key: 'finance-auditor',
    roleName: '财务审核',
    scope: '负责清分、发票、对账和财务数据导出',
    members: 4,
    modules: ['平台清分', '发票管理', '历史订单', '异常订单'],
    canEdit: true,
    canApprove: true,
    canExport: true,
    enabled: true,
  },
  {
    key: 'reviewer',
    roleName: '审核专员',
    scope: '负责运营商和电站准入审核，不涉及资金配置',
    members: 6,
    modules: ['运营商审核', '电站审核', '异常订单'],
    canEdit: true,
    canApprove: true,
    canExport: false,
    enabled: true,
  },
  {
    key: 'service',
    roleName: '客服值班',
    scope: '负责订单查询、异常跟进和用户响应',
    members: 8,
    modules: ['工作台总览', '历史订单', '异常订单', '发票管理'],
    canEdit: false,
    canApprove: false,
    canExport: false,
    enabled: true,
  },
]

const cacheKey = buildRequestCacheKey('/admin/settings/permissions', { scope: 'role-permissions' })

const loading = ref(false)
const tableReady = ref(false)
const cacheLabel = ref('')
const roles = ref(readLocalState(STORAGE_KEY, defaultRoles))

const stats = computed(() => [
  {
    label: '岗位角色',
    value: roles.value.length,
    suffix: ' 个',
    tone: 'primary',
    icon: UserFilled,
    trend: '统一授权口径',
    trendLabel: '按岗位分配后台能力',
  },
  {
    label: '可审批岗位',
    value: roles.value.filter((item) => item.canApprove && item.enabled).length,
    suffix: ' 个',
    tone: 'warning',
    icon: Lock,
    trend: '覆盖准入与资金流程',
    trendLabel: '审批权集中在关键岗位',
  },
  {
    label: '可导出岗位',
    value: roles.value.filter((item) => item.canExport && item.enabled).length,
    suffix: ' 个',
    tone: 'success',
    icon: RefreshRight,
    trend: '支撑复盘与归档',
    trendLabel: '控制敏感数据外发范围',
  },
  {
    label: '已启用岗位',
    value: roles.value.filter((item) => item.enabled).length,
    suffix: ' 个',
    tone: 'info',
    icon: Setting,
    trend: '当前值班配置',
    trendLabel: '停用岗位不会出现在权限分配中',
  },
])

const normalizeRoles = (items = []) => {
  if (!Array.isArray(items) || !items.length) {
    return defaultRoles.map((item) => ({ ...item }))
  }

  return items.map((item, index) => ({
    key: item.key || `role-${index + 1}`,
    roleName: item.roleName || item.role_name || item.name || `岗位 ${index + 1}`,
    scope: item.scope || item.description || '未补充岗位说明',
    members: Number(item.members || item.memberCount || 0),
    modules: Array.isArray(item.modules) ? item.modules : [],
    canEdit: Boolean(item.canEdit ?? item.can_edit ?? false),
    canApprove: Boolean(item.canApprove ?? item.can_approve ?? false),
    canExport: Boolean(item.canExport ?? item.can_export ?? false),
    enabled: Boolean(item.enabled ?? true),
  }))
}

const applyRoles = (items = [], updatedAt = Date.now()) => {
  roles.value = normalizeRoles(items)
  writeLocalState(STORAGE_KEY, roles.value)
  tableReady.value = true
  cacheLabel.value = formatCacheLabel(updatedAt)
}

const loadData = async ({ background = false, force = false } = {}) => {
  const cached = getRequestCache(cacheKey, { ttl: CACHE_TTL, allowStale: true })
  if (cached && !force) {
    applyRoles(cached.value, cached.updatedAt)
  }

  loading.value = force || !cached || !background
  try {
    const { data } = await fetchAdminPermissionSettings()
    const payload = data?.data?.roles || data?.data?.items || []
    applyRoles(payload, Date.now())
    setRequestCache(cacheKey, roles.value)
  } catch (error) {
    if (!roles.value.length) {
      applyRoles(readLocalState(STORAGE_KEY, defaultRoles), Date.now())
    }
  } finally {
    loading.value = false
  }
}

const save = async () => {
  loading.value = true
  try {
    await updateAdminPermissionSettings({ roles: roles.value })
    ElMessage.success('岗位权限配置已保存')
  } catch (error) {
    writeLocalState(STORAGE_KEY, roles.value)
    ElMessage.success('后端暂未返回成功，已先保存当前岗位权限配置')
  } finally {
    setRequestCache(cacheKey, roles.value)
    cacheLabel.value = formatCacheLabel(Date.now())
    loading.value = false
  }
}

onMounted(() => loadData({ background: true }))
onActivated(() => {
  if (shouldRefreshRequestCache(cacheKey, CACHE_TTL)) {
    loadData({ background: true })
  }
})
</script>

<template>
  <div class="page-shell permission-page">
    <PageSectionHeader
      eyebrow="系统配置"
      title="后台岗位权限"
      description="按岗位角色配置可见模块、审批权限和导出能力，让授权对象与业务职责一一对应。"
      chip="角色与权限配置"
    >
      <template #actions>
        <el-tag v-if="cacheLabel" type="info" effect="plain">{{ cacheLabel }}</el-tag>
        <el-button :icon="RefreshRight" :loading="loading" @click="loadData({ force: true })">刷新</el-button>
      </template>
    </PageSectionHeader>

    <section class="stats-grid stats-grid--permissions">
      <MetricCard v-for="item in stats" :key="item.label" v-bind="item" />
    </section>

    <section class="permission-summary-grid">
      <article class="page-panel surface-card">
        <div class="panel-heading">
          <div>
            <h3 class="panel-heading__title">配置原则</h3>
            <p class="panel-heading__desc">将后台授权聚焦到“谁负责什么”，避免出现难以解释的技术开关矩阵。</p>
          </div>
        </div>
        <div class="summary-list">
          <div class="summary-item">
            <strong>查看范围</strong>
            <p>按岗位暴露工作台、订单、清分和审核模块，减少无关页面干扰。</p>
          </div>
          <div class="summary-item">
            <strong>审批权限</strong>
            <p>仅平台管理员、财务审核、审核专员保留审批能力，职责边界更清晰。</p>
          </div>
          <div class="summary-item">
            <strong>导出控制</strong>
            <p>导出权限默认只向财务和平台管理员开放，降低敏感数据外泄风险。</p>
          </div>
        </div>
      </article>
    </section>

    <section class="page-panel surface-card">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">岗位权限配置</h3>
          <p class="panel-heading__desc">直接展示每个岗位能访问哪些模块、是否可审批、是否可导出。</p>
        </div>
        <div class="toolbar-actions">
          <el-button type="primary" :loading="loading" @click="save">保存配置</el-button>
        </div>
      </div>

      <TableSkeletonBlock v-if="loading && !tableReady" :rows="6" :columns="6" />

      <el-table v-else :data="roles" v-loading="loading" stripe>
        <el-table-column prop="roleName" label="岗位角色" min-width="150" />
        <el-table-column prop="scope" label="岗位职责" min-width="220" show-overflow-tooltip />
        <el-table-column label="可见模块" min-width="280">
          <template #default="{ row }">
            <div class="module-tags">
              <el-tag v-for="module in row.modules" :key="module" size="small" effect="plain">{{ module }}</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="在岗人数" width="110" align="center">
          <template #default="{ row }">{{ row.members }} 人</template>
        </el-table-column>
        <el-table-column label="可编辑" width="110" align="center">
          <template #default="{ row }">
            <el-switch v-model="row.canEdit" />
          </template>
        </el-table-column>
        <el-table-column label="可审批" width="110" align="center">
          <template #default="{ row }">
            <el-switch v-model="row.canApprove" />
          </template>
        </el-table-column>
        <el-table-column label="可导出" width="110" align="center">
          <template #default="{ row }">
            <el-switch v-model="row.canExport" />
          </template>
        </el-table-column>
        <el-table-column label="启用状态" width="110" align="center">
          <template #default="{ row }">
            <el-switch v-model="row.enabled" />
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

.permission-summary-grid {
  display: grid;
  gap: 18px;
}

.summary-list {
  display: grid;
  gap: 14px;
}

.summary-item {
  padding: 14px 16px;
  border: 1px solid var(--color-border);
  border-radius: 14px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.9), rgba(245, 248, 252, 0.92));
}

.summary-item strong {
  color: var(--color-text);
}

.summary-item p {
  margin: 8px 0 0;
  color: var(--color-text-2);
  line-height: 1.6;
}

.module-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
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
