<script setup>
import { computed, onActivated, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { DocumentChecked, Edit, Location, RefreshRight } from '@element-plus/icons-vue'

import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import TableSkeletonBlock from '../../components/console/TableSkeletonBlock.vue'
import { fetchOperatorPricingTemplates } from '../../api/operator'
import { getFallbackStationOptions } from '../../utils/stationFallbacks'
import {
  applyLocalTemplateToStations,
  getLocalPricingTemplates,
  mergePricingTemplates,
  saveLocalPricingTemplate,
} from '../../utils/pricingTemplateStore'
import { buildRequestCacheKey, formatCacheUpdatedAt, getRequestCache, setRequestCache } from '../../utils/requestCache'

const CACHE_TTL = 60 * 1000

const loading = ref(false)
const pageReady = ref(false)
const cacheLabel = ref('')
const templates = ref([])
const activeTemplateId = ref(null)
const dialogVisible = ref(false)
const selectedStations = ref([])

const form = reactive({
  periods: [],
})

const cacheKey = buildRequestCacheKey('/operator/pricing/templates', { scope: 'pricing-settings' })
const stationOptions = computed(() => getFallbackStationOptions().filter((item) => Number(item.status) === 0 || item.is_local_draft))
const activeTemplate = computed(() => templates.value.find((item) => String(item.id) === String(activeTemplateId.value)) || null)

const stats = computed(() => [
  { label: '模板总数', value: templates.value.length, suffix: ' 个', tone: 'primary' },
  { label: '启用模板', value: templates.value.filter((item) => item.status === 'active').length, suffix: ' 个', tone: 'success' },
  { label: '指定站点模板', value: templates.value.filter((item) => item.scope === 'station').length, suffix: ' 个', tone: 'warning' },
  { label: '当前模板站点数', value: activeTemplate.value?.stations || 0, suffix: ' 座', tone: 'info' },
])

const normalizePeriods = (template) =>
  (template?.periods || []).map((item) => ({
    id: item.id,
    type: item.type,
    type_text: item.type_text,
    time_range: item.time_range,
    ele_fee: Number(item.ele_fee || 0),
    service_fee: Number(item.service_fee || 0),
  }))

const timeBlocks = computed(() => {
  if (!activeTemplate.value?.periods?.length) {
    return Array.from({ length: 24 }, () => 'flat')
  }
  const blocks = Array.from({ length: 24 }, () => 'flat')
  activeTemplate.value.periods.forEach((period) => {
    if (period.type === 'peak') {
      ;[8, 9, 10, 17, 18, 19, 20].forEach((index) => {
        blocks[index] = 'peak'
      })
    }
    if (period.type === 'valley') {
      ;[0, 1, 2, 3, 4, 5, 6, 22, 23].forEach((index) => {
        blocks[index] = 'valley'
      })
    }
  })
  return blocks
})

const getBlockColor = (type) => {
  if (type === 'peak') return '#ef4444'
  if (type === 'valley') return '#10b981'
  return '#2563eb'
}

const applyTemplates = (items = [], fromCache = false) => {
  templates.value = mergePricingTemplates(items)
  if (!activeTemplateId.value && templates.value.length) {
    activeTemplateId.value = templates.value[0].id
  }
  if (activeTemplate.value) {
    form.periods = normalizePeriods(activeTemplate.value)
  }
  pageReady.value = true
  cacheLabel.value = `${fromCache ? '缓存结果' : '最近刷新'} ${formatCacheUpdatedAt(Date.now())}`
}

const loadData = async ({ background = false } = {}) => {
  const cached = getRequestCache(cacheKey, { ttl: CACHE_TTL, allowStale: true })
  if (cached) {
    applyTemplates(cached.value, true)
    cacheLabel.value = `缓存结果 ${formatCacheUpdatedAt(cached.updatedAt)}`
  }

  loading.value = !cached || !background
  try {
    const res = await fetchOperatorPricingTemplates()
    const items = Array.isArray(res?.data?.data) ? res.data.data : getLocalPricingTemplates()
    applyTemplates(items)
    setRequestCache(cacheKey, items)
    cacheLabel.value = `最近刷新 ${formatCacheUpdatedAt(Date.now())}`
  } catch (error) {
    if (!templates.value.length) {
      applyTemplates(getLocalPricingTemplates())
      cacheLabel.value = '当前内容可用'
    }
  } finally {
    loading.value = false
  }
}

const selectTemplate = (template) => {
  activeTemplateId.value = template.id
  form.periods = normalizePeriods(template)
}

const savePeriods = () => {
  if (!activeTemplate.value) return
  const total = form.periods.reduce((sum, item) => sum + Number(item.ele_fee || 0) + Number(item.service_fee || 0), 0)
  const saved = saveLocalPricingTemplate({
    ...activeTemplate.value,
    periods: form.periods,
    peak_price: Math.max(...form.periods.map((item) => Number(item.ele_fee || 0))),
    flat_price: form.periods.find((item) => item.type === 'flat')?.ele_fee ?? activeTemplate.value.flat_price,
    valley_price: form.periods.find((item) => item.type === 'valley')?.ele_fee ?? activeTemplate.value.valley_price,
    service_price: Number((total / Math.max(form.periods.length, 1) / 2).toFixed(2)),
  })
  selectTemplate(saved)
  cacheLabel.value = '本地配置'
  ElMessage.success('计费模板已保存')
}

const openStationDialog = () => {
  if (!activeTemplate.value) {
    ElMessage.warning('请先选择模板')
    return
  }
  selectedStations.value = []
  dialogVisible.value = true
}

const handleSelectedStations = (rows) => {
  selectedStations.value = rows
}

const submitStationApply = () => {
  if (!activeTemplate.value || !selectedStations.value.length) {
    ElMessage.warning('请至少选择一个电站')
    return
  }
  applyLocalTemplateToStations(activeTemplate.value.id, selectedStations.value.map((item) => item.id))
  dialogVisible.value = false
  ElMessage.success(`已将模板应用到 ${selectedStations.value.length} 个电站`)
}

onMounted(loadData)
onActivated(() => loadData({ background: true }))
</script>

<template>
  <div class="page-shell">
    <PageSectionHeader eyebrow="计费管理" title="电价设置" description="维护峰平谷价格与服务费，并支持将模板应用到指定电站。" chip="电价策略">
      <template #actions>
        <el-tag v-if="cacheLabel" type="info" effect="plain">{{ cacheLabel }}</el-tag>
        <el-button :icon="RefreshRight" :loading="loading" @click="loadData()">刷新</el-button>
      </template>
    </PageSectionHeader>

    <section class="stats-grid stats-grid--pricing">
      <MetricCard v-for="item in stats" :key="item.label" :label="item.label" :value="item.value" :suffix="item.suffix" :tone="item.tone" />
    </section>

    <section class="page-panel surface-card">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">模板选择</h3>
          <p class="panel-heading__desc">选择模板后可直接编辑时段价格并下发到站点。</p>
        </div>
      </div>

      <TableSkeletonBlock v-if="loading && !pageReady" :rows="3" :columns="4" />

      <div v-else class="template-grid">
        <button
          v-for="item in templates"
          :key="item.id"
          type="button"
          class="template-card"
          :class="{ 'template-card--active': String(activeTemplateId) === String(item.id) }"
          @click="selectTemplate(item)"
        >
          <div class="template-card__head">
            <strong>{{ item.name }}</strong>
            <span>{{ item.status === 'active' ? '启用中' : '草稿' }}</span>
          </div>
          <p>{{ item.description || '适用于差异化计费场景' }}</p>
          <div class="template-card__meta">
            <span>{{ item.scope === 'station' ? '指定站点' : '全站通用' }}</span>
            <span>{{ item.updated_at }}</span>
          </div>
        </button>
      </div>
    </section>

    <section class="page-panel surface-card" v-if="activeTemplate">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">规则编辑（{{ activeTemplate.name }}）</h3>
          <p class="panel-heading__desc">支持直接维护峰平谷电价与服务费。</p>
        </div>
        <div class="toolbar-actions">
          <el-button plain :icon="Location" @click="openStationDialog">应用到指定电站</el-button>
          <el-button type="primary" :icon="Edit" @click="savePeriods">保存规则</el-button>
        </div>
      </div>

      <div class="visual-wrapper">
        <div class="time-labels">
          <span>00:00</span>
          <span>12:00</span>
          <span>24:00</span>
        </div>
        <div class="rainbow-bar">
          <div v-for="(type, index) in timeBlocks" :key="index" class="color-block" :style="{ backgroundColor: getBlockColor(type) }" />
        </div>
        <div class="legend-group">
          <div class="legend-item"><div class="color-dot" style="background: #ef4444;" />高峰</div>
          <div class="legend-item"><div class="color-dot" style="background: #2563eb;" />平段</div>
          <div class="legend-item"><div class="color-dot" style="background: #10b981;" />低谷</div>
        </div>
      </div>

      <el-table :data="form.periods" border class="pricing-table">
        <el-table-column prop="type_text" label="时段类型" width="120" align="center" />
        <el-table-column prop="time_range" label="生效时间范围" min-width="220" />
        <el-table-column label="电价（元/kWh）" width="180">
          <template #default="{ row }">
            <el-input-number v-model="row.ele_fee" :step="0.01" :min="0" style="width: 100%" />
          </template>
        </el-table-column>
        <el-table-column label="服务费（元/kWh）" width="180">
          <template #default="{ row }">
            <el-input-number v-model="row.service_fee" :step="0.01" :min="0" style="width: 100%" />
          </template>
        </el-table-column>
        <el-table-column label="合计（元/kWh）" width="150" align="center">
          <template #default="{ row }">{{ (Number(row.ele_fee || 0) + Number(row.service_fee || 0)).toFixed(2) }}</template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog v-model="dialogVisible" title="应用到指定电站" width="640px">
      <div class="dialog-tip">
        当前模板：<strong>{{ activeTemplate?.name || '-' }}</strong>
      </div>
      <el-table :data="stationOptions" border height="320" @selection-change="handleSelectedStations">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="station_name" label="电站名称" min-width="220" />
        <el-table-column prop="status_text" label="状态" width="120" align="center" />
        <el-table-column prop="price_template_name" label="当前模板" min-width="160" />
      </el-table>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitStationApply">确认应用</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.stats-grid--pricing {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.template-card {
  text-align: left;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 16px;
  padding: 16px;
  background: #fff;
  cursor: pointer;
  transition: all 0.2s ease;
}

.template-card--active {
  border-color: rgba(37, 99, 235, 0.32);
  box-shadow: 0 12px 24px rgba(37, 99, 235, 0.12);
}

.template-card__head,
.template-card__meta,
.legend-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.template-card p {
  color: var(--color-text-2);
  margin: 10px 0;
}

.visual-wrapper {
  margin-bottom: 24px;
  background: #fafafa;
  padding: 20px;
  border-radius: 12px;
  border: 1px solid #ebeef5;
}

.time-labels {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}

.rainbow-bar {
  display: flex;
  height: 36px;
  border-radius: 6px;
  overflow: hidden;
  background: #ebeef5;
}

.color-block {
  flex: 1;
}

.legend-group {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-top: 14px;
}

.color-dot {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  margin-right: 8px;
}

.pricing-table {
  margin-bottom: 8px;
}

.dialog-tip {
  margin-bottom: 12px;
  color: var(--color-text-2);
}

@media (max-width: 1280px) {
  .stats-grid--pricing,
  .template-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .stats-grid--pricing,
  .template-grid {
    grid-template-columns: 1fr;
  }
}
</style>
