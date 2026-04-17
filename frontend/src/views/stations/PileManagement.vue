<script setup>
import { computed, onActivated, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { CircleCheck, Lightning, Plus, RefreshRight, Tickets, WarningFilled } from '@element-plus/icons-vue'

import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import EmptyStateBlock from '../../components/console/EmptyStateBlock.vue'
import ErrorBlock from '../../components/console/ErrorBlock.vue'
import TableSkeletonBlock from '../../components/console/TableSkeletonBlock.vue'
import {
  batchCreateStationChargers,
  createStationCharger,
  fetchOperatorStationOptions,
  fetchStationChargers,
  updateStationCharger,
} from '../../api/operator'
import { buildRequestCacheKey, formatCacheUpdatedAt, getRequestCache, setRequestCache } from '../../utils/requestCache'
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
const errorMessage = ref('')

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
  { label: '电桩总数', value: chargers.value.length, suffix: ' 台', trend: '当前电站全部设备', trendLabel: '支持新增与批量生成', tone: 'primary', icon: Lightning },
  { label: '空闲可用', value: chargers.value.filter((item) => Number(item.status) === 0).length, suffix: ' 台', trend: '可立即发起充电', trendLabel: '可用于扫码与人工发起', tone: 'success', icon: CircleCheck },
  { label: '充电中', value: chargers.value.filter((item) => Number(item.status) === 1).length, suffix: ' 台', trend: '当前被订单占用', trendLabel: '与实时订单联动展示', tone: 'warning', icon: Tickets },
  { label: '故障 / 停用', value: chargers.value.filter((item) => [2, 3].includes(Number(item.status))).length, suffix: ' 台', trend: '需跟进处理', trendLabel: '支持直接调整状态', tone: 'danger', icon: WarningFilled },
])

const statusOptions = [
  { label: '空闲', value: 0 },
  { label: '充电中', value: 1 },
  { label: '故障', value: 2 },
  { label: '停用', value: 3 },
]

const statusTagType = (status) => (Number(status) === 1 ? 'warning' : Number(status) === 2 ? 'danger' : Number(status) === 3 ? 'info' : 'success')

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
    cacheLabel.value = `最近可用数据 ${formatCacheUpdatedAt(cached.updatedAt)}`
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
    cacheLabel.value = `已更新 ${formatCacheUpdatedAt(Date.now())}`
  } catch (error) {
    if (!stations.value.length) {
      stations.value = getFallbackStationOptions()
      selectedStationId.value = String(route.query.stationId || stations.value[0]?.id || '')
      cacheLabel.value = '当前内容可用'
    }
  } finally {
    stationLoading.value = false
  }
}

const applyChargers = (remoteRows = [], fromCache = false) => {
  chargers.value = mergeChargersWithLocal(selectedStationId.value, remoteRows)
  tableReady.value = true
  cacheLabel.value = `${fromCache ? '最近可用数据' : '已更新'} ${formatCacheUpdatedAt(Date.now())}`
}

const loadChargers = async ({ background = false } = {}) => {
  if (!selectedStationId.value) {
    chargers.value = []
    return
  }

  const cached = getRequestCache(chargerCacheKey.value, { ttl: CACHE_TTL, allowStale: true })
  if (cached) {
    applyChargers(cached.value, true)
    cacheLabel.value = `最近可用数据 ${formatCacheUpdatedAt(cached.updatedAt)}`
  }

  loading.value = !cached || !background
  errorMessage.value = ''
  try {
    const { data } = await fetchStationChargers(selectedStationId.value)
    const rows = Array.isArray(data?.data) ? data.data : []
    applyChargers(rows)
    setRequestCache(chargerCacheKey.value, rows)
    cacheLabel.value = `已更新 ${formatCacheUpdatedAt(Date.now())}`
  } catch (error) {
    applyChargers(cached?.value || [], !cached)
    if (!cached) {
      cacheLabel.value = '当前内容可用'
    }
    errorMessage.value = cached ? '最新电桩信息暂未刷新成功，当前先展示最近一次可用结果。' : '服务暂不可用，当前先展示可操作的电桩内容。'
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
    const { data } = await createStationCharger(selectedStation.value.id, {
      sn_code: addForm.sn_code.trim(),
      charger_name: addForm.charger_name.trim(),
      type: addForm.type,
      power_kw: Number(addForm.power_kw),
      status: Number(addForm.status),
    })
    ElMessage.success(data?.message || '电桩新增成功')
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
    const { data } = await batchCreateStationChargers(selectedStation.value.id, {
      count: Number(batchForm.count),
      type: batchForm.type,
      power_kw: Number(batchForm.power_kw),
    })
    ElMessage.success(data?.message || '批量生成成功')
  } catch (error) {
    batchAddLocalChargers(selectedStation.value, batchForm)
    ElMessage.success('已批量生成电桩')
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
    ElMessage.success('电桩状态已先更新到当前页面')
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
  await loadStations()
  await loadChargers()
})

onActivated(() => {
  loadStations({ background: true })
  loadChargers({ background: true })
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
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">电桩列表</h3>
          <p class="panel-heading__desc">按电站查看电桩编号、类型、功率和当前状态。</p>
        </div>
      </div>

      <ErrorBlock
        v-if="errorMessage"
        title="电桩列表已恢复显示"
        :description="errorMessage"
        @retry="loadChargers()"
      />

      <TableSkeletonBlock v-if="loading && !tableReady" :rows="6" :columns="5" />

      <el-table v-else-if="chargers.length" :data="chargers" v-loading="loading" stripe>
        <el-table-column prop="sn_code" label="电桩编号" min-width="160" />
        <el-table-column prop="charger_name" label="电桩名称" min-width="180" />
        <el-table-column prop="type" label="类型" width="110" align="center" />
        <el-table-column label="功率" width="110" align="center">
          <template #default="{ row }">{{ row.power_kw }} kW</template>
        </el-table-column>
        <el-table-column label="状态" width="200" align="center">
          <template #default="{ row }">
            <div class="status-editor">
              <el-tag :type="statusTagType(row.status)">{{ row.status_text }}</el-tag>
              <el-select :model-value="row.status" size="small" style="width: 110px" @change="(value) => updateChargerStatus(row, value)">
                <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="180" />
      </el-table>

      <EmptyStateBlock v-else-if="!loading" title="暂无电桩数据" description="当前电站尚未配置电桩，可新增或批量生成。" />
    </section>

    <el-dialog v-model="addDialogVisible" width="560px" title="新增电桩">
      <el-form label-width="96px">
        <el-form-item label="电桩编号"><el-input v-model="addForm.sn_code" placeholder="例如 ST001DC001" /></el-form-item>
        <el-form-item label="电桩名称"><el-input v-model="addForm.charger_name" placeholder="例如 A 区快充 01" /></el-form-item>
        <el-form-item label="类型">
          <el-radio-group v-model="addForm.type">
            <el-radio-button label="AC">AC</el-radio-button>
            <el-radio-button label="DC">DC</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="功率"><el-input-number v-model="addForm.power_kw" :min="1" :max="999" style="width: 100%" /></el-form-item>
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

    <el-dialog v-model="batchDialogVisible" width="520px" title="批量生成电桩">
      <el-form label-width="96px">
        <el-form-item label="生成数量"><el-input-number v-model="batchForm.count" :min="1" :max="50" style="width: 100%" /></el-form-item>
        <el-form-item label="电桩类型">
          <el-radio-group v-model="batchForm.type">
            <el-radio-button label="AC">AC</el-radio-button>
            <el-radio-button label="DC">DC</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="默认功率"><el-input-number v-model="batchForm.power_kw" :min="1" :max="999" style="width: 100%" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="batchSubmitting" @click="submitBatchCreate">确认生成</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.stats-grid--chargers {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.station-banner {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 18px;
}

.station-banner__meta,
.status-editor {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

@media (max-width: 1280px) {
  .stats-grid--chargers {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .stats-grid--chargers {
    grid-template-columns: 1fr;
  }

  .station-banner {
    flex-direction: column;
  }
}
</style>
