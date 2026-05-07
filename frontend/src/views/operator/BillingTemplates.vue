<script setup>
import { computed, onActivated, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Edit, Location, Plus, RefreshRight } from '@element-plus/icons-vue'

import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import TableSkeletonBlock from '../../components/console/TableSkeletonBlock.vue'
import EmptyStateBlock from '../../components/console/EmptyStateBlock.vue'
import {
  bindStationTemplate,
  createBillingTemplate,
  deleteBillingTemplate,
  fetchOperatorStationOptions,
  fetchBillingTemplates,
  updateBillingTemplate,
  updateBillingTemplateStatus,
} from '../../api/operator'
import { buildRequestCacheKey, clearRequestCache, formatCacheLabel, getRequestCache, setRequestCache } from '../../utils/requestCache'

const CACHE_TTL = 60 * 1000

const loading = ref(false)
const tableReady = ref(false)
const rows = ref([])
const stationRows = ref([])
const cacheLabel = ref('')
const dialogVisible = ref(false)
const stationDialogVisible = ref(false)
const editingId = ref(null)
const saving = ref(false)
const applying = ref(false)
const applyingTemplate = ref(null)
const selectedStations = ref([])

const form = reactive({
  name: '',
  peak_price: 1.88,
  flat_price: 1.32,
  valley_price: 0.68,
  service_price: 0.8,
  scope: 'station',
  status: 'active',
})

const cacheKey = buildRequestCacheKey('/operator/billing/templates', { scope: 'billing-templates' })
const stationOptions = computed(() => stationRows.value.filter((item) => Number(item.status) === 0))

const stats = computed(() => [
  { label: '模板总数', value: rows.value.length, suffix: ' 个', tone: 'primary', icon: Document, trend: '统一维护计费模板', trendLabel: '支持电站复用' },
  { label: '启用模板', value: rows.value.filter((item) => item.status === 'active').length, suffix: ' 个', tone: 'success', icon: RefreshRight, trend: '可绑定到电站', trendLabel: '停用后不建议新绑定' },
  { label: '已绑定电站', value: rows.value.reduce((sum, item) => sum + Number(item.bound_station_count || 0), 0), suffix: ' 座', tone: 'warning', icon: Location, trend: '模板应用范围', trendLabel: '与电站列表保持一致' },
  { label: '平均服务费', value: rows.value.length ? (rows.value.reduce((sum, item) => sum + Number(item.service_price || 0), 0) / rows.value.length).toFixed(2) : '0.00', prefix: '¥', tone: 'info', icon: Edit, trend: '当前模板均值', trendLabel: '便于对比价格策略' },
])

const resetForm = () => {
  editingId.value = null
  Object.assign(form, {
    name: '',
    peak_price: 1.88,
    flat_price: 1.32,
    valley_price: 0.68,
    service_price: 0.8,
    scope: 'station',
    status: 'active',
  })
}

const applyRows = (items = [], updatedAt = Date.now()) => {
  rows.value = Array.isArray(items) ? items : []
  tableReady.value = true
  cacheLabel.value = formatCacheLabel(updatedAt)
}

const loadData = async ({ background = false, force = false } = {}) => {
  const cached = getRequestCache(cacheKey, { ttl: CACHE_TTL, allowStale: true })
  if (cached && !force) applyRows(cached.value, cached.updatedAt)
  loading.value = !cached || !background || force
  try {
    const { data } = await fetchBillingTemplates()
    if (data?.code !== 200) throw new Error(data?.message || '模板列表加载失败')
    const items = Array.isArray(data?.data) ? data.data : []
    applyRows(items)
    setRequestCache(cacheKey, items)
  } catch (error) {
    if (!rows.value.length) {
      applyRows([])
      ElMessage.error(error?.message || '模板列表加载失败')
    }
  } finally {
    loading.value = false
  }
}

const loadStationOptions = async () => {
  try {
    const { data } = await fetchOperatorStationOptions()
    if (data?.code !== 200) throw new Error(data?.message || '电站选项加载失败')
    stationRows.value = Array.isArray(data?.data) ? data.data : []
  } catch (error) {
    stationRows.value = []
    ElMessage.error(error?.message || '电站选项加载失败')
  }
}

const openCreate = () => {
  resetForm()
  dialogVisible.value = true
}

const openEdit = (row) => {
  editingId.value = row.id
  Object.assign(form, {
    name: row.name,
    peak_price: row.peak_price,
    flat_price: row.flat_price,
    valley_price: row.valley_price,
    service_price: row.service_price,
    scope: row.scope || 'station',
    status: row.status || 'active',
  })
  dialogVisible.value = true
}

const save = async () => {
  if (!form.name.trim()) {
    ElMessage.warning('请填写模板名称')
    return
  }
  saving.value = true
  try {
    const action = editingId.value ? updateBillingTemplate(editingId.value, form) : createBillingTemplate(form)
    const { data } = await action
    if (data?.code !== 200) throw new Error(data?.message || '模板保存失败')
    clearRequestCache('/operator/billing/templates')
    clearRequestCache('/operator/pricing/templates')
    dialogVisible.value = false
    ElMessage.success(data?.message || '模板已保存')
    await loadData({ force: true })
  } catch (error) {
    ElMessage.error(error?.message || '模板保存失败')
  } finally {
    saving.value = false
  }
}

const toggleStatus = async (row) => {
  const nextStatus = row.status === 'active' ? 'disabled' : 'active'
  try {
    await ElMessageBox.confirm(`确认${nextStatus === 'active' ? '启用' : '停用'}模板「${row.name}」？`, '模板状态', { type: 'warning' })
    const { data } = await updateBillingTemplateStatus(row.id, nextStatus)
    if (data?.code !== 200) throw new Error(data?.message || '模板状态更新失败')
    ElMessage.success(data?.message || '模板状态已更新')
    await loadData({ force: true })
  } catch (error) {
    if (error !== 'cancel') ElMessage.error(error?.message || '模板状态更新失败')
  }
}

const removeTemplate = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除或停用模板「${row.name}」？`, '删除模板', { type: 'warning' })
    const { data } = await deleteBillingTemplate(row.id)
    if (data?.code !== 200) throw new Error(data?.message || '模板删除失败')
    ElMessage.success(data?.message || '模板已处理')
    await loadData({ force: true })
  } catch (error) {
    if (error !== 'cancel') ElMessage.error(error?.message || '模板删除失败')
  }
}

const openStationDialog = async (row) => {
  applyingTemplate.value = row
  selectedStations.value = []
  stationDialogVisible.value = true
  await loadStationOptions()
}

const submitStationApply = async () => {
  if (!applyingTemplate.value || !selectedStations.value.length) {
    ElMessage.warning('请至少选择一个电站')
    return
  }
  applying.value = true
  try {
    for (const station of selectedStations.value) {
      const { data } = await bindStationTemplate(station.id, applyingTemplate.value.id)
      if (data?.code !== 200) throw new Error(data?.message || '模板应用失败')
    }
    clearRequestCache('/operator/stations')
    stationDialogVisible.value = false
    ElMessage.success(`已应用到 ${selectedStations.value.length} 座电站`)
    await loadData({ force: true })
    await loadStationOptions()
  } catch (error) {
    ElMessage.error(error?.message || '模板应用失败')
  } finally {
    applying.value = false
  }
}

onMounted(async () => {
  await loadData()
  await loadStationOptions()
})
onActivated(() => {
  loadData({ background: true })
  loadStationOptions()
})
</script>

<template>
  <div class="page-shell">
    <PageSectionHeader eyebrow="计费管理" title="电价模板管理" description="维护可复用的计费模板，并支持下发到指定电站。" chip="模板中心">
      <template #actions>
        <el-tag v-if="cacheLabel" type="info" effect="plain">{{ cacheLabel }}</el-tag>
        <el-button :icon="RefreshRight" :loading="loading" @click="loadData({ force: true })">刷新</el-button>
        <el-button type="primary" :icon="Plus" @click="openCreate">新建模板</el-button>
      </template>
    </PageSectionHeader>

    <section class="stats-grid stats-grid--billing">
      <MetricCard v-for="item in stats" :key="item.label" v-bind="item" />
    </section>

    <section class="page-panel surface-card table-shell">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">模板列表</h3>
          <p class="panel-heading__desc">展示峰平谷电价、服务费和已绑定电站情况。</p>
        </div>
      </div>

      <TableSkeletonBlock v-if="loading && !tableReady" :rows="6" :columns="9" />
      <el-table v-else-if="rows.length" :data="rows" v-loading="loading" stripe>
        <el-table-column prop="name" label="模板名称" min-width="180" />
        <el-table-column prop="peak_price" label="峰段" width="90" align="center" />
        <el-table-column prop="flat_price" label="平段" width="90" align="center" />
        <el-table-column prop="valley_price" label="谷段" width="90" align="center" />
        <el-table-column prop="service_price" label="服务费" width="100" align="center" />
        <el-table-column label="绑定电站" min-width="190">
          <template #default="{ row }">
            <div class="cell-stack">
              <strong>{{ row.bound_station_count || 0 }} 座</strong>
              <span>{{ row.bound_station_names || '暂未绑定电站' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">{{ row.status === 'active' ? '启用' : '停用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="170" />
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link :type="row.status === 'active' ? 'warning' : 'success'" @click="toggleStatus(row)">
              {{ row.status === 'active' ? '停用' : '启用' }}
            </el-button>
            <el-button link type="primary" @click="openStationDialog(row)">查看/绑定电站</el-button>
            <el-button link type="danger" @click="removeTemplate(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <EmptyStateBlock v-else-if="!loading" title="暂无电价模板" description="可新建模板后绑定到电站。" />
    </section>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑模板' : '新建模板'" width="560px">
      <div class="form-grid">
        <el-form-item label="模板名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="适用范围">
          <el-select v-model="form.scope" style="width: 100%">
            <el-option label="全站通用" value="all" />
            <el-option label="指定电站" value="station" />
          </el-select>
        </el-form-item>
        <el-form-item label="峰段电价"><el-input-number v-model="form.peak_price" :step="0.01" style="width: 100%" /></el-form-item>
        <el-form-item label="平段电价"><el-input-number v-model="form.flat_price" :step="0.01" style="width: 100%" /></el-form-item>
        <el-form-item label="谷段电价"><el-input-number v-model="form.valley_price" :step="0.01" style="width: 100%" /></el-form-item>
        <el-form-item label="服务费"><el-input-number v-model="form.service_price" :step="0.01" style="width: 100%" /></el-form-item>
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="stationDialogVisible" title="绑定电站" width="680px">
      <div class="dialog-tip">当前模板：<strong>{{ applyingTemplate?.name || '-' }}</strong></div>
      <el-table :data="stationOptions" border height="320" @selection-change="(rows) => { selectedStations = rows }">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="station_name" label="电站名称" min-width="220" />
        <el-table-column prop="status_text" label="状态" width="120" align="center" />
        <el-table-column prop="price_template_name" label="当前模板" min-width="180" />
      </el-table>
      <template #footer>
        <el-button @click="stationDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="applying" @click="submitStationApply">确认绑定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.stats-grid--billing {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.dialog-tip,
.cell-stack span {
  color: var(--color-text-2);
}

.cell-stack {
  display: grid;
  gap: 4px;
}

@media (max-width: 1280px) {
  .stats-grid--billing {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .stats-grid--billing,
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
