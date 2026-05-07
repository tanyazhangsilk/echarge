<script setup>
import { computed, onActivated, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Edit, Location, RefreshRight } from '@element-plus/icons-vue'

import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import TableSkeletonBlock from '../../components/console/TableSkeletonBlock.vue'
import EmptyStateBlock from '../../components/console/EmptyStateBlock.vue'
import {
  bindStationTemplate,
  fetchOperatorPricingTemplates,
  fetchOperatorStationOptions,
  updateBillingTemplate,
} from '../../api/operator'
import { buildRequestCacheKey, clearRequestCache, formatCacheLabel, getRequestCache, setRequestCache } from '../../utils/requestCache'

const CACHE_TTL = 60 * 1000

const loading = ref(false)
const saving = ref(false)
const applying = ref(false)
const pageReady = ref(false)
const cacheLabel = ref('')
const templates = ref([])
const stationRows = ref([])
const activeTemplateId = ref(null)
const dialogVisible = ref(false)
const selectedStations = ref([])

const form = reactive({
  periods: [],
})

const TIME_SEGMENTS = [
  { id: 1, type: 'valley', type_text: '谷段', time_range: '00:00-07:00' },
  { id: 2, type: 'flat', type_text: '平段', time_range: '07:00-10:00' },
  { id: 3, type: 'peak', type_text: '峰段', time_range: '10:00-15:00' },
  { id: 4, type: 'flat', type_text: '平段', time_range: '15:00-18:00' },
  { id: 5, type: 'peak', type_text: '峰段', time_range: '18:00-21:00' },
  { id: 6, type: 'valley', type_text: '谷段', time_range: '21:00-24:00' },
]

const cacheKey = buildRequestCacheKey('/operator/pricing/templates', { scope: 'pricing-settings' })
const stationOptions = computed(() => stationRows.value.filter((item) => Number(item.status) === 0))
const activeTemplate = computed(() => templates.value.find((item) => String(item.id) === String(activeTemplateId.value)) || null)

const stats = computed(() => [
  { label: '模板总数', value: templates.value.length, suffix: ' 个', tone: 'primary' },
  { label: '启用模板', value: templates.value.filter((item) => item.status === 'active').length, suffix: ' 个', tone: 'success' },
  { label: '站点模板', value: templates.value.filter((item) => item.scope === 'station').length, suffix: ' 个', tone: 'warning' },
  { label: '绑定电站', value: Number(activeTemplate.value?.bound_station_count || activeTemplate.value?.stations || 0), suffix: ' 座', tone: 'info' },
])

const buildFallbackPeriods = (template) => {
  const peak = Number(template?.peak_price || 0)
  const flat = Number(template?.flat_price || 0)
  const valley = Number(template?.valley_price || 0)
  const service = Number(template?.service_price || 0)

  return TIME_SEGMENTS.map((segment) => ({
    ...segment,
    ele_fee: segment.type === 'peak' ? peak : segment.type === 'valley' ? valley : flat,
    service_fee: service,
  }))
}

const normalizePeriods = (template) => {
  const source = Array.isArray(template?.periods) && template.periods.length ? template.periods : buildFallbackPeriods(template)
  return source.map((item, index) => ({
    id: item.id ?? index + 1,
    type: item.type || TIME_SEGMENTS[index]?.type || 'flat',
    type_text: item.type_text || TIME_SEGMENTS[index]?.type_text || '平段',
    time_range: item.time_range || TIME_SEGMENTS[index]?.time_range || '',
    ele_fee: Number(item.ele_fee ?? item.price ?? 0),
    service_fee: Number(item.service_fee ?? template?.service_price ?? 0),
  }))
}

const parseHour = (value) => Number(String(value).split(':')[0] || 0)

const timeBlocks = computed(() => {
  const periods = form.periods.length ? form.periods : normalizePeriods(activeTemplate.value)
  const blocks = Array.from({ length: 24 }, () => 'flat')

  periods.forEach((period) => {
    const [startText, endText] = String(period.time_range || '').split('-')
    const start = parseHour(startText)
    const endRaw = parseHour(endText)
    const end = endRaw === 0 && String(endText || '').startsWith('24') ? 24 : endRaw
    for (let hour = start; hour < end; hour += 1) {
      if (hour >= 0 && hour < 24) blocks[hour] = period.type || 'flat'
    }
  })

  return blocks
})

const getBlockColor = (type) => {
  if (type === 'peak') return '#ef4444'
  if (type === 'valley') return '#10b981'
  return '#2563eb'
}

const applyTemplates = (items = [], updatedAt = Date.now()) => {
  templates.value = Array.isArray(items) ? items : []
  if (!templates.value.length) {
    activeTemplateId.value = null
    form.periods = []
    pageReady.value = true
    cacheLabel.value = formatCacheLabel(updatedAt)
    return
  }

  if (!templates.value.some((item) => String(item.id) === String(activeTemplateId.value))) {
    activeTemplateId.value = templates.value[0].id
  }
  form.periods = normalizePeriods(activeTemplate.value)
  pageReady.value = true
  cacheLabel.value = formatCacheLabel(updatedAt)
}

const loadData = async ({ background = false, force = false } = {}) => {
  const cached = getRequestCache(cacheKey, { ttl: CACHE_TTL, allowStale: true })
  if (cached && !force) applyTemplates(cached.value, cached.updatedAt)

  loading.value = !cached || !background || force
  try {
    const { data } = await fetchOperatorPricingTemplates()
    if (data?.code !== 200) throw new Error(data?.message || '电价模板加载失败')
    const items = Array.isArray(data?.data) ? data.data : []
    applyTemplates(items)
    setRequestCache(cacheKey, items)
  } catch (error) {
    if (!templates.value.length) {
      applyTemplates([])
      ElMessage.error(error?.message || '电价模板加载失败')
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

const selectTemplate = (template) => {
  activeTemplateId.value = template.id
  form.periods = normalizePeriods(template)
}

const savePeriods = async () => {
  if (!activeTemplate.value) return

  const peakRows = form.periods.filter((item) => item.type === 'peak')
  const flatRows = form.periods.filter((item) => item.type === 'flat')
  const valleyRows = form.periods.filter((item) => item.type === 'valley')
  const avgServicePrice = form.periods.length
    ? Number((form.periods.reduce((sum, item) => sum + Number(item.service_fee || 0), 0) / form.periods.length).toFixed(2))
    : Number(activeTemplate.value.service_price || 0)

  const payload = {
    name: activeTemplate.value.name,
    peak_price: Number((peakRows[0]?.ele_fee ?? activeTemplate.value.peak_price ?? 0).toFixed(2)),
    flat_price: Number((flatRows[0]?.ele_fee ?? activeTemplate.value.flat_price ?? 0).toFixed(2)),
    valley_price: Number((valleyRows[0]?.ele_fee ?? activeTemplate.value.valley_price ?? 0).toFixed(2)),
    service_price: avgServicePrice,
    scope: activeTemplate.value.scope || 'station',
    status: activeTemplate.value.status || 'active',
  }

  saving.value = true
  try {
    const { data } = await updateBillingTemplate(activeTemplate.value.id, payload)
    if (data?.code !== 200) throw new Error(data?.message || '电价规则保存失败')
    clearRequestCache('/operator/pricing/templates')
    clearRequestCache('/operator/billing/templates')
    await loadData({ force: true })
    ElMessage.success(data?.message || '电价规则已保存')
  } catch (error) {
    ElMessage.error(error?.message || '电价规则保存失败')
  } finally {
    saving.value = false
  }
}

const openStationDialog = () => {
  if (!activeTemplate.value) {
    ElMessage.warning('请先选择电价模板')
    return
  }
  selectedStations.value = []
  dialogVisible.value = true
}

const submitStationApply = async () => {
  if (!activeTemplate.value || !selectedStations.value.length) {
    ElMessage.warning('请至少选择一个电站')
    return
  }

  applying.value = true
  try {
    for (const station of selectedStations.value) {
      const { data } = await bindStationTemplate(station.id, activeTemplate.value.id)
      if (data?.code !== 200) throw new Error(data?.message || '模板绑定失败')
    }
    clearRequestCache('/operator/stations')
    clearRequestCache('/operator/pricing/templates')
    clearRequestCache('/operator/billing/templates')
    dialogVisible.value = false
    await loadStationOptions()
    await loadData({ force: true })
    ElMessage.success(`已绑定 ${selectedStations.value.length} 座电站`)
  } catch (error) {
    ElMessage.error(error?.message || '模板绑定失败')
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
    <PageSectionHeader eyebrow="计费管理" title="电价设置" description="查看并维护运营商的分时电价规则，支持直接保存到模板并下发到电站。" chip="计费规则">
      <template #actions>
        <el-tag v-if="cacheLabel" type="info" effect="plain">{{ cacheLabel }}</el-tag>
        <el-button :icon="RefreshRight" :loading="loading" @click="loadData({ force: true })">刷新</el-button>
      </template>
    </PageSectionHeader>

    <section class="stats-grid stats-grid--pricing">
      <MetricCard v-for="item in stats" :key="item.label" :label="item.label" :value="item.value" :suffix="item.suffix" :tone="item.tone" />
    </section>

    <section class="page-panel surface-card">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">模板列表</h3>
          <p class="panel-heading__desc">选择模板后可直接查看峰平谷规则并保存调整。</p>
        </div>
      </div>

      <TableSkeletonBlock v-if="loading && !pageReady" :rows="3" :columns="4" />
      <div v-else-if="templates.length" class="template-grid">
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
            <span>{{ item.status === 'active' ? '启用中' : '已停用' }}</span>
          </div>
          <p>{{ item.description || '分时电价与服务费模板' }}</p>
          <div class="template-card__meta">
            <span>{{ item.scope === 'station' ? '指定电站' : '全站通用' }}</span>
            <span>{{ item.bound_station_count || item.stations || 0 }} 座电站</span>
          </div>
        </button>
      </div>
      <EmptyStateBlock v-else-if="!loading" title="暂无电价模板" description="可先到模板管理页创建电价模板。" />
    </section>

    <section v-if="activeTemplate" class="page-panel surface-card">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">规则编辑：{{ activeTemplate.name }}</h3>
          <p class="panel-heading__desc">修改峰平谷电价与服务费后，将同步更新当前模板。</p>
        </div>
        <div class="toolbar-actions">
          <el-button plain :icon="Location" @click="openStationDialog">绑定电站</el-button>
          <el-button type="primary" :icon="Edit" :loading="saving" @click="savePeriods">保存规则</el-button>
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
          <div class="legend-item"><div class="color-dot" style="background: #ef4444;" />峰段</div>
          <div class="legend-item"><div class="color-dot" style="background: #2563eb;" />平段</div>
          <div class="legend-item"><div class="color-dot" style="background: #10b981;" />谷段</div>
        </div>
      </div>

      <el-table :data="form.periods" border class="pricing-table">
        <el-table-column prop="type_text" label="时段类型" width="120" align="center" />
        <el-table-column prop="time_range" label="时间范围" min-width="220" />
        <el-table-column label="电费单价 (元/kWh)" width="180">
          <template #default="{ row }">
            <el-input-number v-model="row.ele_fee" :step="0.01" :min="0" style="width: 100%" />
          </template>
        </el-table-column>
        <el-table-column label="服务费 (元/kWh)" width="180">
          <template #default="{ row }">
            <el-input-number v-model="row.service_fee" :step="0.01" :min="0" style="width: 100%" />
          </template>
        </el-table-column>
        <el-table-column label="合计单价 (元/kWh)" width="160" align="center">
          <template #default="{ row }">{{ (Number(row.ele_fee || 0) + Number(row.service_fee || 0)).toFixed(2) }}</template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog v-model="dialogVisible" title="绑定电站" width="640px">
      <div class="dialog-tip">
        当前模板：<strong>{{ activeTemplate?.name || '-' }}</strong>
      </div>
      <el-table :data="stationOptions" border height="320" @selection-change="(rows) => { selectedStations = rows }">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="station_name" label="电站名称" min-width="220" />
        <el-table-column prop="status_text" label="状态" width="120" align="center" />
        <el-table-column prop="price_template_name" label="当前模板" min-width="160" />
      </el-table>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="applying" @click="submitStationApply">确认绑定</el-button>
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
