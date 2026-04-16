<script setup>
import { computed, onActivated, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Connection, Grid, OfficeBuilding, Plus, RefreshRight, SetUp, View } from '@element-plus/icons-vue'

import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import EmptyStateBlock from '../../components/console/EmptyStateBlock.vue'
import TableSkeletonBlock from '../../components/console/TableSkeletonBlock.vue'
import {
  applyOperatorStation,
  bindStationTemplate,
  fetchOperatorPricingTemplates,
  fetchOperatorStations,
  fetchStationChargers,
  updateStationVisibility,
} from '../../api/operator'
import { buildRequestCacheKey, formatCacheUpdatedAt, getRequestCache, setRequestCache } from '../../utils/requestCache'
import { saveStationApplicationDraft } from '../../utils/stationApplicationDrafts'
import { mergeChargersWithLocal } from '../../utils/chargerDemoStore'
import { getFallbackStationRows } from '../../utils/stationFallbacks'
import { applyLocalTemplateToStations, mergePricingTemplates } from '../../utils/pricingTemplateStore'

const router = useRouter()
const CACHE_TTL = 45 * 1000

const loading = ref(false)
const tableReady = ref(false)
const errorMessage = ref('')
const stations = ref([])
const total = ref(0)
const cacheLabel = ref('')

const chargerLoading = ref(false)
const chargers = ref([])
const chargerDrawerVisible = ref(false)
const currentStation = ref(null)

const templateLoading = ref(false)
const templates = ref([])
const templateDialogVisible = ref(false)
const bindSubmitting = ref(false)
const bindForm = reactive({ templateId: null })

const applyDialogVisible = ref(false)
const applySubmitting = ref(false)
const applyForm = reactive({
  station_name: '',
  province: '',
  city: '',
  district: '',
  address: '',
  longitude: 114.0579,
  latitude: 22.5431,
  contact_name: '',
  contact_phone: '',
  operation_hours: '00:00-24:00',
  parking_fee_desc: '',
  station_remark: '',
  planned_charger_count: 4,
  total_power_kw: 240,
  cover_image: '',
  site_photos_text: '',
  qualification_remark: '',
})

const pagination = reactive({ page: 1, pageSize: 10 })
const filters = reactive({ keyword: '', status: '', visibility: '' })
const summary = reactive({ total_count: 0, online_count: 0, pending_count: 0, private_count: 0 })

let searchTimer = null

const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '已审核通过', value: 0 },
  { label: '待审核', value: 3 },
  { label: '已驳回', value: 4 },
]

const visibilityOptions = [
  { label: '全部可见性', value: '' },
  { label: '公开站点', value: 'public' },
  { label: '未公开', value: 'private' },
]

const stats = computed(() => [
  { label: '电站总数', value: summary.total_count, suffix: ' 座', trend: '当前主体全部电站', trendLabel: '含本地申请与演示站点', tone: 'primary', icon: OfficeBuilding },
  { label: '已审核通过', value: summary.online_count, suffix: ' 座', trend: '可继续配置电桩与模板', trendLabel: '支持正式运营', tone: 'success', icon: Grid },
  { label: '待审核', value: summary.pending_count, suffix: ' 座', trend: '等待平台处理', trendLabel: '支持查看完整申请信息', tone: 'warning', icon: View },
  { label: '未公开', value: summary.private_count, suffix: ' 座', trend: '当前不对外展示', trendLabel: '可按策略切换为公开站点', tone: 'info', icon: Connection },
])

const selectedTemplate = computed(() => templates.value.find((item) => String(item.id) === String(bindForm.templateId)) || null)
const chargerSummary = computed(() => ({
  total: chargers.value.length,
  charging: chargers.value.filter((item) => Number(item.status) === 1).length,
  idle: chargers.value.filter((item) => Number(item.status) === 0).length,
  fault: chargers.value.filter((item) => Number(item.status) === 2).length,
}))

const queryParams = computed(() => ({
  page: pagination.page,
  page_size: pagination.pageSize,
  keyword: filters.keyword.trim() || undefined,
  status: filters.status === '' ? undefined : Number(filters.status),
  visibility: filters.visibility || undefined,
}))

const queryCacheKey = computed(() => buildRequestCacheKey('/operator/stations', queryParams.value))

const statusTagType = (status) => (Number(status) === 0 ? 'success' : Number(status) === 3 ? 'warning' : Number(status) === 4 ? 'danger' : 'info')
const visibilityTagType = (visibility) => (visibility === 'public' ? 'success' : 'info')
const chargerStatusType = (status) => (Number(status) === 1 ? 'warning' : Number(status) === 2 ? 'danger' : Number(status) === 3 ? 'info' : 'success')

const resetApplyForm = () => {
  Object.assign(applyForm, {
    station_name: '',
    province: '',
    city: '',
    district: '',
    address: '',
    longitude: 114.0579,
    latitude: 22.5431,
    contact_name: '',
    contact_phone: '',
    operation_hours: '00:00-24:00',
    parking_fee_desc: '',
    station_remark: '',
    planned_charger_count: 4,
    total_power_kw: 240,
    cover_image: '',
    site_photos_text: '',
    qualification_remark: '',
  })
}

const refreshSummary = (items) => {
  summary.total_count = items.length
  summary.online_count = items.filter((item) => Number(item.status) === 0).length
  summary.pending_count = items.filter((item) => Number(item.status) === 3).length
  summary.private_count = items.filter((item) => item.visibility !== 'public').length
}

const applyPayload = (payload = {}, fromCache = false) => {
  const items = Array.isArray(payload.items) ? payload.items : []
  stations.value = items
  total.value = Number(payload.total || items.length)
  pagination.page = Number(payload.page || pagination.page)
  pagination.pageSize = Number(payload.page_size || pagination.pageSize)
  Object.assign(summary, payload.summary || {})
  refreshSummary(items)
  tableReady.value = true
  cacheLabel.value = `${fromCache ? '缓存结果' : '最近刷新'} ${formatCacheUpdatedAt(Date.now())}`
}

const loadStations = async ({ background = false, force = false } = {}) => {
  const cached = getRequestCache(queryCacheKey.value, { ttl: CACHE_TTL, allowStale: true })

  if (cached && !force) {
    applyPayload(cached.value, true)
    cacheLabel.value = `缓存结果 ${formatCacheUpdatedAt(cached.updatedAt)}`
  }

  loading.value = !cached || force || !background
  errorMessage.value = ''

  try {
    const { data } = await fetchOperatorStations(queryParams.value)
    const payload = data?.data || getFallbackStationRows(queryParams.value)
    applyPayload(payload)
    setRequestCache(queryCacheKey.value, payload)
    cacheLabel.value = `最近刷新 ${formatCacheUpdatedAt(Date.now())}`
  } catch (error) {
    const fallback = getFallbackStationRows(queryParams.value)
    if (!stations.value.length) {
      applyPayload(fallback)
      cacheLabel.value = '演示数据'
    }
    errorMessage.value = cached ? '已显示最近一次结果，后台刷新失败' : '电站列表已切换为演示与本地申请数据'
  } finally {
    loading.value = false
  }
}

const loadTemplates = async () => {
  if (templateLoading.value) return
  templateLoading.value = true
  try {
    const { data } = await fetchOperatorPricingTemplates()
    templates.value = mergePricingTemplates(data?.data || [])
  } catch (error) {
    templates.value = mergePricingTemplates([])
  } finally {
    templateLoading.value = false
  }
}

const openChargerDrawer = async (station) => {
  currentStation.value = station
  chargerDrawerVisible.value = true
  chargerLoading.value = true
  try {
    const { data } = await fetchStationChargers(station.id)
    chargers.value = mergeChargersWithLocal(station.id, data?.data || [])
  } catch (error) {
    chargers.value = mergeChargersWithLocal(station.id, [])
  } finally {
    chargerLoading.value = false
  }
}

const handleVisibilityChange = async (station, visibility) => {
  try {
    await ElMessageBox.confirm(`确认调整“${station.station_name}”的公开状态吗？`, '修改可见性', {
      type: 'warning',
      confirmButtonText: '确认',
      cancelButtonText: '取消',
    })
    const { data } = await updateStationVisibility(station.id, visibility)
    ElMessage.success(data?.message || '站点可见性已更新')
    await loadStations({ force: true })
  } catch (error) {
    if (error !== 'cancel') {
      station.visibility = visibility
      station.visibility_text = visibility === 'public' ? '公开站点' : '未公开'
      ElMessage.success('站点可见性已先更新到当前页面')
      await loadStations({ background: true })
    }
  }
}

const openBindDialog = async (station) => {
  if (Number(station.status) !== 0 || station.is_local_draft) {
    ElMessage.warning('仅已审核通过的电站可以绑定电价模板')
    return
  }
  currentStation.value = station
  bindForm.templateId = station.price_template_id || null
  templateDialogVisible.value = true
  if (!templates.value.length) loadTemplates()
}

const submitBindTemplate = async () => {
  if (!currentStation.value || !bindForm.templateId) {
    ElMessage.warning('请选择电价模板')
    return
  }

  bindSubmitting.value = true
  try {
    const { data } = await bindStationTemplate(currentStation.value.id, bindForm.templateId)
    ElMessage.success(data?.message || '模板绑定成功')
  } catch (error) {
    applyLocalTemplateToStations(bindForm.templateId, [currentStation.value.id])
    ElMessage.success('模板已先绑定到当前电站')
  } finally {
    bindSubmitting.value = false
    templateDialogVisible.value = false
    await loadStations({ force: true })
  }
}

const submitApplyStation = async () => {
  const requiredFields = [
    ['station_name', '请输入电站名称'],
    ['province', '请输入省份'],
    ['city', '请输入城市'],
    ['district', '请输入区县'],
    ['address', '请输入详细地址'],
    ['contact_name', '请输入联系人'],
    ['contact_phone', '请输入联系电话'],
  ]

  for (const [field, message] of requiredFields) {
    if (!String(applyForm[field] || '').trim()) {
      ElMessage.warning(message)
      return
    }
  }

  const payload = {
    station_name: applyForm.station_name.trim(),
    province: applyForm.province.trim(),
    city: applyForm.city.trim(),
    district: applyForm.district.trim(),
    address: applyForm.address.trim(),
    longitude: Number(applyForm.longitude),
    latitude: Number(applyForm.latitude),
    contact_name: applyForm.contact_name.trim(),
    contact_phone: applyForm.contact_phone.trim(),
    operation_hours: applyForm.operation_hours.trim(),
    parking_fee_desc: applyForm.parking_fee_desc.trim(),
    station_remark: applyForm.station_remark.trim(),
    planned_charger_count: Number(applyForm.planned_charger_count),
    total_power_kw: Number(applyForm.total_power_kw),
    cover_image: applyForm.cover_image.trim(),
    site_photos: applyForm.site_photos_text.split('\n').map((item) => item.trim()).filter(Boolean),
    qualification_remark: applyForm.qualification_remark.trim(),
  }

  applySubmitting.value = true
  try {
    saveStationApplicationDraft(payload)
    const { data } = await applyOperatorStation(payload)
    ElMessage.success(data?.message || '电站申请已提交')
  } catch (error) {
    saveStationApplicationDraft(payload)
    ElMessage.success('电站申请已保存在本地审核链路')
  } finally {
    applySubmitting.value = false
    applyDialogVisible.value = false
    pagination.page = 1
    await loadStations({ force: true })
  }
}

const resetFilters = () => {
  filters.keyword = ''
  filters.status = ''
  filters.visibility = ''
}

const openPileManagement = (station) => {
  router.push(`/operator/stations/chargers?stationId=${station.id}`)
}

watch(
  () => [filters.keyword, filters.status, filters.visibility],
  () => {
    if (searchTimer) clearTimeout(searchTimer)
    searchTimer = setTimeout(() => {
      pagination.page = 1
      loadStations()
    }, 240)
  },
)

onMounted(loadStations)
onActivated(() => loadStations({ background: true }))
onBeforeUnmount(() => {
  if (searchTimer) clearTimeout(searchTimer)
})
</script>

<template>
  <div class="page-shell station-page">
    <PageSectionHeader eyebrow="资产管理" title="电站管理" description="维护电站申请、审核状态、公开配置与模板绑定。" chip="电站中心">
      <template #actions>
        <el-button type="primary" :icon="Plus" @click="resetApplyForm(); applyDialogVisible = true">申请新建电站</el-button>
        <el-button :icon="RefreshRight" :loading="loading" @click="loadStations({ force: true })">刷新列表</el-button>
      </template>
    </PageSectionHeader>

    <section class="stats-grid stats-grid--stations">
      <MetricCard v-for="item in stats" :key="item.label" v-bind="item" />
    </section>

    <section class="page-panel surface-card">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">筛选条件</h3>
          <p class="panel-heading__desc">支持按电站名称、地址、状态和可见性快速检索。</p>
        </div>
        <div class="toolbar-actions">
          <el-tag v-if="cacheLabel" type="info" effect="plain">{{ cacheLabel }}</el-tag>
          <el-button @click="resetFilters">重置</el-button>
        </div>
      </div>

      <div class="filter-row">
        <el-input v-model="filters.keyword" clearable placeholder="搜索电站名称、地址或模板" style="width: 340px" />
        <el-select v-model="filters.status" placeholder="选择状态" clearable style="width: 160px">
          <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="filters.visibility" placeholder="选择可见性" clearable style="width: 160px">
          <el-option v-for="item in visibilityOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
      </div>
    </section>

    <section class="page-panel surface-card table-shell">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">电站列表</h3>
          <p class="panel-heading__desc">共 {{ total }} 条记录。</p>
        </div>
      </div>

      <el-alert v-if="errorMessage" :title="errorMessage" type="warning" show-icon :closable="false" class="panel-alert" />

      <TableSkeletonBlock v-if="loading && !tableReady" :rows="6" :columns="8" />

      <el-table v-else-if="stations.length" :data="stations" v-loading="loading" stripe>
        <el-table-column label="电站信息" min-width="250">
          <template #default="{ row }">
            <div class="cell-stack">
              <div class="station-title">
                <strong>{{ row.station_name }}</strong>
                <el-tag v-if="row.is_local_draft" type="warning" size="small">本地申请</el-tag>
              </div>
              <span>{{ row.full_address }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="联系人" min-width="170">
          <template #default="{ row }">
            <div class="cell-stack">
              <strong>{{ row.contact_name || '-' }}</strong>
              <span>{{ row.contact_phone || '-' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="电桩规模" width="150" align="center">
          <template #default="{ row }">{{ row.charger_count || row.planned_charger_count || 0 }} 枪</template>
        </el-table-column>
        <el-table-column label="审核状态" width="120" align="center">
          <template #default="{ row }"><el-tag :type="statusTagType(row.status)">{{ row.status_text }}</el-tag></template>
        </el-table-column>
        <el-table-column label="公开状态" width="120" align="center">
          <template #default="{ row }"><el-tag :type="visibilityTagType(row.visibility)">{{ row.visibility_text }}</el-tag></template>
        </el-table-column>
        <el-table-column label="当前模板" min-width="160">
          <template #default="{ row }">{{ row.price_template_name || '未绑定模板' }}</template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="180" />
        <el-table-column label="操作" min-width="300" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openChargerDrawer(row)">查看电桩</el-button>
            <el-button link type="primary" @click="openPileManagement(row)">管理电桩</el-button>
            <el-button link type="success" @click="openBindDialog(row)">绑定模板</el-button>
            <el-dropdown trigger="click">
              <el-button link type="info">更多操作</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="handleVisibilityChange(row, row.visibility === 'public' ? 'private' : 'public')">
                    {{ row.visibility === 'public' ? '设为未公开' : '设为公开站点' }}
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <EmptyStateBlock v-else-if="!loading" title="暂无电站数据" description="可通过“申请新建电站”补充主业务链路。" />

      <div class="pager">
        <el-pagination
          :current-page="pagination.page"
          :page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="(page) => { pagination.page = page; loadStations() }"
          @size-change="(size) => { pagination.page = 1; pagination.pageSize = size; loadStations() }"
        />
      </div>
    </section>

    <el-drawer v-model="chargerDrawerVisible" size="720px" :title="`${currentStation?.station_name || ''} 电桩概览`">
      <div class="station-summary surface-card" v-if="currentStation">
        <div>
          <strong>{{ currentStation.station_name }}</strong>
          <p>{{ currentStation.full_address }}</p>
        </div>
        <div class="summary-tags">
          <el-tag>总数 {{ chargerSummary.total }}</el-tag>
          <el-tag type="success">空闲 {{ chargerSummary.idle }}</el-tag>
          <el-tag type="warning">充电中 {{ chargerSummary.charging }}</el-tag>
          <el-tag type="danger">故障 {{ chargerSummary.fault }}</el-tag>
        </div>
      </div>

      <el-table :data="chargers" v-loading="chargerLoading" stripe>
        <el-table-column prop="sn_code" label="电桩编号" min-width="150" />
        <el-table-column prop="charger_name" label="电桩名称" min-width="160" />
        <el-table-column prop="type" label="类型" width="90" align="center" />
        <el-table-column label="功率" width="110" align="center">
          <template #default="{ row }">{{ row.power_kw }} kW</template>
        </el-table-column>
        <el-table-column label="状态" width="120" align="center">
          <template #default="{ row }"><el-tag :type="chargerStatusType(row.status)">{{ row.status_text }}</el-tag></template>
        </el-table-column>
      </el-table>
    </el-drawer>

    <el-dialog v-model="templateDialogVisible" title="绑定电价模板" width="560px">
      <el-form label-width="96px">
        <el-form-item label="当前电站">
          <div>{{ currentStation?.station_name || '-' }}</div>
        </el-form-item>
        <el-form-item label="选择模板">
          <el-select v-model="bindForm.templateId" style="width: 100%" :loading="templateLoading" placeholder="请选择电价模板">
            <el-option v-for="item in templates" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="模板说明">
          <div class="text-muted">{{ selectedTemplate?.description || '选择后可立即同步到当前电站。' }}</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="templateDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="bindSubmitting" @click="submitBindTemplate">确认绑定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="applyDialogVisible" title="申请新建电站" width="780px">
      <el-form label-width="110px" class="apply-form-grid">
        <el-form-item label="电站名称"><el-input v-model="applyForm.station_name" /></el-form-item>
        <el-form-item label="省 / 市 / 区">
          <div class="inline-grid">
            <el-input v-model="applyForm.province" placeholder="省份" />
            <el-input v-model="applyForm.city" placeholder="城市" />
            <el-input v-model="applyForm.district" placeholder="区县" />
          </div>
        </el-form-item>
        <el-form-item label="详细地址" class="apply-form-grid__full"><el-input v-model="applyForm.address" /></el-form-item>
        <el-form-item label="经度"><el-input-number v-model="applyForm.longitude" :step="0.0001" style="width: 100%" /></el-form-item>
        <el-form-item label="纬度"><el-input-number v-model="applyForm.latitude" :step="0.0001" style="width: 100%" /></el-form-item>
        <el-form-item label="联系人"><el-input v-model="applyForm.contact_name" /></el-form-item>
        <el-form-item label="联系电话"><el-input v-model="applyForm.contact_phone" /></el-form-item>
        <el-form-item label="营业时间"><el-input v-model="applyForm.operation_hours" /></el-form-item>
        <el-form-item label="停车费说明"><el-input v-model="applyForm.parking_fee_desc" /></el-form-item>
        <el-form-item label="规划电桩数"><el-input-number v-model="applyForm.planned_charger_count" :min="1" style="width: 100%" /></el-form-item>
        <el-form-item label="规划总功率"><el-input-number v-model="applyForm.total_power_kw" :min="1" style="width: 100%" /></el-form-item>
        <el-form-item label="封面占位"><el-input v-model="applyForm.cover_image" placeholder="可填写图片说明或占位 URL" /></el-form-item>
        <el-form-item label="现场图片占位"><el-input v-model="applyForm.site_photos_text" type="textarea" :rows="4" placeholder="每行一条图片说明或占位链接" /></el-form-item>
        <el-form-item label="站点说明" class="apply-form-grid__full"><el-input v-model="applyForm.station_remark" type="textarea" :rows="4" /></el-form-item>
        <el-form-item label="资质补充说明" class="apply-form-grid__full"><el-input v-model="applyForm.qualification_remark" type="textarea" :rows="4" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="applyDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="applySubmitting" @click="submitApplyStation">提交申请</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.stats-grid--stations {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.filter-row,
.inline-grid,
.summary-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.inline-grid > * {
  flex: 1 1 0;
}

.cell-stack {
  display: grid;
  gap: 4px;
}

.station-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.panel-alert {
  margin-bottom: 16px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.station-summary {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 18px;
  margin-bottom: 16px;
}

.apply-form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 4px 18px;
}

.apply-form-grid__full {
  grid-column: 1 / -1;
}

.text-muted {
  color: var(--color-text-2);
}

@media (max-width: 1280px) {
  .stats-grid--stations,
  .apply-form-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .stats-grid--stations,
  .apply-form-grid {
    grid-template-columns: 1fr;
  }

  .station-summary {
    flex-direction: column;
  }
}
</style>
