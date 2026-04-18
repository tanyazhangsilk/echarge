<script setup>
import { computed, onActivated, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { CircleCheck, Lightning, Plus, RefreshRight, Tickets, WarningFilled } from '@element-plus/icons-vue'

import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import EmptyStateBlock from '../../components/console/EmptyStateBlock.vue'
import TableSkeletonBlock from '../../components/console/TableSkeletonBlock.vue'
import {
  batchCreateStationChargers,
  createStationCharger,
  fetchOperatorStationOptions,
  fetchStationChargers,
  updateStationCharger,
} from '../../api/operator'
import { buildRequestCacheKey, formatCacheLabel, getRequestCache, setRequestCache, shouldRefreshRequestCache } from '../../utils/requestCache'
import { addLocalCharger, batchAddLocalChargers, mergeChargersWithLocal, updateLocalChargerStatus } from '../../utils/chargerDemoStore'
import { getFallbackStationOptions } from '../../utils/stationFallbacks'

const route = useRoute()
const CACHE_TTL = 60 * 1000

const stationLoading = ref(false)
const loading = ref(false)
const submitLoading = ref(false)
const batchSubmitting = ref(false)
const tableReady = ref(false)
const cacheLabel = ref('')

const stations = ref([])
const chargers = ref([])
const selectedStationId = ref(null)

const addDialogVisible = ref(false)
const batchDialogVisible = ref(false)

const addForm = reactive({
  sn_code: '',
  charger_name: '',
  type: 'DC',
  power_kw: 120,
  status: 0,
})

const batchForm = reactive({
  count: 5,
  type: 'DC',
  power_kw: 120,
})

const selectedStation = computed(() => stations.value.find((item) => String(item.id) === String(selectedStationId.value)) || null)
const stationCacheKey = computed(() => buildRequestCacheKey('/operator/stations/options', { scope: 'pile-management' }))
const chargerCacheKey = computed(() => buildRequestCacheKey(`/operator/stations/${selectedStationId.value}/chargers`, { station_id: selectedStationId.value }))

const chargerStats = computed(() => [
  {
    label: '电桩总数',
    value: chargers.value.length,
    suffix: ' 台',
    trend: '当前电站全部设备',
    trendLabel: '支持新增与批量生成',
    tone: 'primary',
    icon: Lightning,
  },
  {
    label: '空闲可用',
    value: chargers.value.filter((item) => Number(item.status) === 0).length,
    suffix: ' 台',
    trend: '可立即发起充电',
    trendLabel: '用于扫码与手动发起',
    tone: 'success',
    icon: CircleCheck,
  },
  {
    label: '充电中',
    value: chargers.value.filter((item) => Number(item.status) === 1).length,
    suffix: ' 台',
    trend: '当前被订单占用',
    trendLabel: '与实时订单联动展示',
    tone: 'warning',
    icon: Tickets,
  },
  {
    label: '故障 / 停用',
    value: chargers.value.filter((item) => [2, 3].includes(Number(item.status))).length,
    suffix: ' 台',
    trend: '需跟进处理',
    trendLabel: '支持直接调整状态',
    tone: 'danger',
    icon: WarningFilled,
  },
])

const statusOptions = [
  { label: '空闲', value: 0 },
  { label: '充电中', value: 1 },
  { label: '故障', value: 2 },
  { label: '停用', value: 3 },
]

const statusTagType = (status) => (Number(status) === 1 ? 'warning' : Number(status) === 2 ? 'danger' : Number(status) === 3 ? 'info' : 'success')

const updateCacheLabel = (timestamp = Date.now()) => {
  cacheLabel.value = formatCacheLabel(timestamp)
}

const resetAddForm = () => {
  Object.assign(addForm, {
    sn_code: '',
    charger_name: '',
    type: 'DC',
    power_kw: 120,
    status: 0,
  })
}

const loadStations = async ({ background = false } = {}) => {
  const cached = getRequestCache(stationCacheKey.value, { ttl: CACHE_TTL, allowStale: true })
  if (cached) {
    stations.value = Array.isArray(cached.value) && cached.value.length ? cached.value : getFallbackStationOptions()
    if (!selectedStationId.value && stations.value.length) {
      selectedStationId.value = String(route.query.stationId || '') || String(stations.value[0].id)
    }
    updateCacheLabel(cached.updatedAt)
  }

  stationLoading.value = !cached || !background
  try {
    const { data } = await fetchOperatorStationOptions()
    const items = Array.isArray(data?.data) && data.data.length ? data.data : getFallbackStationOptions()
    stations.value = items
    if (String(route.query.stationId || '') && items.some((item) => String(item.id) === String(route.query.stationId))) {
      selectedStationId.value = String(route.query.stationId)
    } else if (!selectedStationId.value && items.length) {
      selectedStationId.value = String(items[0].id)
    }
    setRequestCache(stationCacheKey.value, items)
    updateCacheLabel(Date.now())
  } catch (error) {
    if (!stations.value.length) {
      stations.value = getFallbackStationOptions()
      selectedStationId.value = String(route.query.stationId || stations.value[0]?.id || '')
      updateCacheLabel(Date.now())
    }
  } finally {
    stationLoading.value = false
  }
}

const applyChargers = (remoteRows = [], updatedAt = Date.now()) => {
  chargers.value = mergeChargersWithLocal(selectedStationId.value, remoteRows)
  tableReady.value = true
  updateCacheLabel(updatedAt)
}

const loadChargers = async ({ background = false } = {}) => {
  if (!selectedStationId.value) {
    chargers.value = []
    return
  }

  const cached = getRequestCache(chargerCacheKey.value, { ttl: CACHE_TTL, allowStale: true })
  if (cached) {
    applyChargers(cached.value, cached.updatedAt)
  }

  loading.value = !cached || !background
  try {
    const { data } = await fetchStationChargers(selectedStationId.value)
    const rows = Array.isArray(data?.data) ? data.data : []
    applyChargers(rows, Date.now())
    setRequestCache(chargerCacheKey.value, rows)
  } catch (error) {
    applyChargers(cached?.value || [], Date.now())
  } finally {
    loading.value = false
  }
}

const openAddDialog = () => {
  if (!selectedStation.value) {
    ElMessage.warning('请先选择电站')
    return
  }
  resetAddForm()
  addDialogVisible.value = true
}

const submitAddCharger = async () => {
  if (!selectedStation.value) {
    ElMessage.warning('请先选择电站')
    return
  }
  if (!addForm.sn_code.trim() || !addForm.charger_name.trim()) {
    ElMessage.warning('请填写电桩编号与名称')
    return
  }

  submitLoading.value = true
  try {
    await createStationCharger(selectedStation.value.id, {
      sn_code: addForm.sn_code.trim(),
      charger_name: addForm.charger_name.trim(),
      type: addForm.type,
      power_kw: Number(addForm.power_kw),
      status: Number(addForm.status),
    })
    ElMessage.success('电桩新增成功')
  } catch (error) {
    addLocalCharger(selectedStation.value, addForm)
    ElMessage.success('电桩已加入当前站点')
  } finally {
    submitLoading.value = false
    addDialogVisible.value = false
    await loadChargers()
  }
}

const openBatchDialog = () => {
  if (!selectedStation.value) {
    ElMessage.warning('请先选择电站')
    return
  }
  Object.assign(batchForm, { count: 5, type: 'DC', power_kw: 120 })
  batchDialogVisible.value = true
}

const submitBatchCreate = async () => {
  if (!selectedStation.value) {
    ElMessage.warning('请先选择电站')
    return
  }

  batchSubmitting.value = true
  try {
    await batchCreateStationChargers(selectedStation.value.id, {
      count: Number(batchForm.count),
      type: batchForm.type,
      power_kw: Number(batchForm.power_kw),
    })
    ElMessage.success('批量生成成功')
  } catch (error) {
    batchAddLocalChargers(selectedStation.value, batchForm)
    ElMessage.success('已批量生成演示电桩')
  } finally {
    batchSubmitting.value = false
    batchDialogVisible.value = false
    await loadChargers()
  }
}

const updateChargerStatus = async (row, status) => {
  try {
    await updateStationCharger(selectedStationId.value, row.id, { status })
    ElMessage.success('电桩状态已更新')
  } catch (error) {
    updateLocalChargerStatus(selectedStationId.value, row.id, status)
    ElMessage.success('电桩状态已更新到当前页面')
  } finally {
    await loadChargers({ background: true })
  }
}

watch(selectedStationId, (value, oldValue) => {
  if (value && value !== oldValue) {
    loadChargers()
  }
})

onMounted(async () => {
  await loadStations({ background: true })
  await loadChargers({ background: true })
})

onActivated(() => {
  if (shouldRefreshRequestCache(stationCacheKey.value, CACHE_TTL)) {
    loadStations({ background: true })
  }
  if (selectedStationId.value && shouldRefreshRequestCache(chargerCacheKey.value, CACHE_TTL)) {
    loadChargers({ background: true })
  }
})
</script>

<template>
  <div class="page-shell charger-page">
    <PageSectionHeader eyebrow="资产管理" title="电桩管理" description="维护单桩新增、批量生成、设备状态与所属电站。" chip="设备配置">
      <template #actions>
        <el-select v-model="selectedStationId" placeholder="请选择电站" filterable :loading="stationLoading" style="width: 300px">
          <el-option v-for="item in stations" :key="item.id" :label="`${item.station_name} / ${item.status_text}`" :value="String(item.id)" />
        </el-select>
        <el-button type="primary" :icon="Plus" @click="openAddDialog">新增电桩</el-button>
        <el-button type="primary" plain :icon="Tickets" @click="openBatchDialog">批量生成电桩</el-button>
        <el-button :icon="RefreshRight" :loading="loading" @click="loadChargers()">刷新</el-button>
      </template>
    </PageSectionHeader>

    <div v-if="selectedStation" class="station-banner surface-card">
      <div>
        <strong>{{ selectedStation.station_name }}</strong>
        <p>{{ selectedStation.full_address || '当前电站地址待补充' }}</p>
      </div>
      <div class="station-banner__meta">
        <el-tag :type="Number(selectedStation.status) === 0 ? 'success' : 'warning'">{{ selectedStation.status_text }}</el-tag>
        <el-tag :type="selectedStation.visibility === 'public' ? 'success' : 'info'">{{ selectedStation.visibility_text }}</el-tag>
        <el-tag v-if="cacheLabel" type="info" effect="plain">{{ cacheLabel }}</el-tag>
      </div>
    </div>

    <section class="stats-grid stats-grid--chargers">
      <MetricCard v-for="item in chargerStats" :key="item.label" v-bind="item" />
    </section>

    <section class="page-panel surface-card table-shell">
      <TableSkeletonBlock v-if="loading && !tableReady" :rows="6" :columns="8" />

      <el-table v-else-if="chargers.length" :data="chargers" v-loading="loading" stripe>
        <el-table-column prop="sn_code" label="设备编号" min-width="180" />
        <el-table-column prop="charger_name" label="设备名称" min-width="160" />
        <el-table-column prop="type" label="类型" width="100" align="center" />
        <el-table-column label="功率(kW)" width="110" align="right">
          <template #default="{ row }">{{ Number(row.power_kw || 0).toFixed(0) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="120" align="center">
          <template #default="{ row }"><el-tag :type="statusTagType(row.status)">{{ row.status_text }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="updated_at" label="最近更新" width="180" />
        <el-table-column label="快捷操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button link type="success" @click="updateChargerStatus(row, 0)">置为空闲</el-button>
            <el-button link type="warning" @click="updateChargerStatus(row, 1)">置为充电中</el-button>
            <el-button link type="danger" @click="updateChargerStatus(row, 2)">标记故障</el-button>
            <el-button link type="info" @click="updateChargerStatus(row, 3)">停用</el-button>
          </template>
        </el-table-column>
      </el-table>

      <EmptyStateBlock v-else-if="!loading" title="暂无电桩数据" description="当前电站下还没有可展示的电桩。" />
    </section>

    <el-dialog v-model="addDialogVisible" title="新增电桩" width="560px">
      <el-form label-width="96px">
        <el-form-item label="设备编号"><el-input v-model="addForm.sn_code" /></el-form-item>
        <el-form-item label="设备名称"><el-input v-model="addForm.charger_name" /></el-form-item>
        <el-form-item label="类型">
          <el-select v-model="addForm.type" style="width: 100%">
            <el-option label="直流 DC" value="DC" />
            <el-option label="交流 AC" value="AC" />
          </el-select>
        </el-form-item>
        <el-form-item label="功率(kW)"><el-input-number v-model="addForm.power_kw" :min="7" :max="360" style="width: 100%" /></el-form-item>
        <el-form-item label="初始状态">
          <el-select v-model="addForm.status" style="width: 100%">
            <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitAddCharger">确认新增</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="batchDialogVisible" title="批量生成演示电桩" width="520px">
      <el-form label-width="110px">
        <el-form-item label="生成数量">
          <el-input-number v-model="batchForm.count" :min="1" :max="50" style="width: 100%" />
        </el-form-item>
        <el-form-item label="设备类型">
          <el-select v-model="batchForm.type" style="width: 100%">
            <el-option label="直流 DC" value="DC" />
            <el-option label="交流 AC" value="AC" />
          </el-select>
        </el-form-item>
        <el-form-item label="默认功率(kW)">
          <el-input-number v-model="batchForm.power_kw" :min="7" :max="360" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="batchSubmitting" @click="submitBatchCreate">开始生成</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.station-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.station-banner strong {
  display: block;
  font-size: 18px;
  margin-bottom: 6px;
}

.station-banner p {
  margin: 0;
  color: var(--color-text-2);
}

.station-banner__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.stats-grid--chargers {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

@media (max-width: 1280px) {
  .stats-grid--chargers {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .station-banner {
    flex-direction: column;
    align-items: flex-start;
  }

  .stats-grid--chargers {
    grid-template-columns: 1fr;
  }
}
</style>
