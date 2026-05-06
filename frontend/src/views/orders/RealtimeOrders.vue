<script setup>
import { computed, onActivated, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DataAnalysis, Lightning, Money, Plus, RefreshRight, Tickets } from '@element-plus/icons-vue'

import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import EmptyStateBlock from '../../components/console/EmptyStateBlock.vue'
import TableSkeletonBlock from '../../components/console/TableSkeletonBlock.vue'
import { finishDemoOrder, markDemoOrderAbnormal, startDemoOrder } from '../../api/demo'
import {
  fetchOperatorOrderStartOptions,
  fetchOperatorRealtimeOrders,
  fetchStationChargers,
} from '../../api/operator'
import {
  buildRequestCacheKey,
  formatCacheLabel,
  getRequestCache,
  setRequestCache,
  shouldRefreshRequestCache,
} from '../../utils/requestCache'
import {
  demoStartUsers,
  finishLocalDemoOrder,
  getDemoOrderListPayload,
  markLocalDemoOrderAbnormal,
  startLocalDemoOrder,
} from '../../utils/demoOrderAdapter'
import { mergeChargersWithLocal } from '../../utils/chargerDemoStore'
import { getFallbackStationOptions } from '../../utils/stationFallbacks'

const router = useRouter()
const CACHE_TTL = 12 * 1000

const loading = ref(false)
const tableReady = ref(false)
const orders = ref([])
const total = ref(0)
const busyOrderId = ref(null)
const cacheLabel = ref('')

const startDialogVisible = ref(false)
const startLoading = ref(false)
const startOptionsLoading = ref(false)
const startMode = ref('manual_demo')
const startUsers = ref([...demoStartUsers])
const startStations = ref(getFallbackStationOptions())
const startChargers = ref([])

const pagination = reactive({ page: 1, pageSize: 10 })
const summary = reactive({
  total_count: 0,
  total_charge_amount: 0,
  total_ele_fee: 0,
  total_service_fee: 0,
})
const startForm = reactive({
  user_id: null,
  station_id: null,
  charger_id: null,
  source_type: 'manual_demo',
})

const queryParams = computed(() => ({ page: pagination.page, page_size: pagination.pageSize }))
const listCacheKey = computed(() => buildRequestCacheKey('/operator/orders/realtime', queryParams.value))
const startCacheKey = computed(() => buildRequestCacheKey('/operator/orders/start-options', { scope: 'start-options' }))
const manualStations = computed(() => startStations.value.filter((item) => Number(item.status) === 0 || item.is_local_draft))
const sourceTypeLabel = computed(() => (startMode.value === 'manual_demo' ? '演示创建订单' : '扫码充电'))

const formatMoney = (value) => `¥${Number(value || 0).toFixed(2)}`

const stats = computed(() => [
  {
    label: '实时订单',
    value: summary.total_count,
    suffix: ' 单',
    trend: '当前处于充电中的订单数',
    trendLabel: '支持结束和异常处理',
    tone: 'primary',
    icon: Lightning,
  },
  {
    label: '实时电量',
    value: Number(summary.total_charge_amount || 0).toFixed(2),
    suffix: ' kWh',
    trend: '实时订单累计电量',
    trendLabel: '用于演示当前负载',
    tone: 'success',
    icon: DataAnalysis,
  },
  {
    label: '实时电费',
    value: Number(summary.total_ele_fee || 0).toFixed(2),
    prefix: '¥',
    trend: '实时订单累计电费',
    trendLabel: '按当前计费结果汇总',
    tone: 'warning',
    icon: Money,
  },
  {
    label: '实时服务费',
    value: Number(summary.total_service_fee || 0).toFixed(2),
    prefix: '¥',
    trend: '实时订单累计服务费',
    trendLabel: '与电费共同构成总额',
    tone: 'info',
    icon: Tickets,
  },
])

const applyPayload = (payload = {}, updatedAt = Date.now()) => {
  orders.value = payload.items || []
  total.value = Number(payload.total || orders.value.length)
  pagination.page = Number(payload.page || pagination.page)
  pagination.pageSize = Number(payload.page_size || pagination.pageSize)
  Object.assign(summary, payload.summary || {})
  tableReady.value = true
  cacheLabel.value = formatCacheLabel(updatedAt)
}

const loadOrders = async ({ background = false } = {}) => {
  const cached = getRequestCache(listCacheKey.value, { ttl: CACHE_TTL, allowStale: true })
  if (cached) {
    applyPayload(cached.value, cached.updatedAt)
  }

  loading.value = !cached || !background
  try {
    const { data } = await fetchOperatorRealtimeOrders(queryParams.value)
    const payload = data?.data || getDemoOrderListPayload('realtime')
    applyPayload(payload, Date.now())
    setRequestCache(listCacheKey.value, payload)
  } catch (error) {
    if (!orders.value.length) {
      const demoPayload = getDemoOrderListPayload('realtime')
      applyPayload({ ...demoPayload, page: 1, page_size: pagination.pageSize }, Date.now())
      if (!demoPayload?.items?.length) {
        ElMessage.error('实时订单加载失败')
      }
    }
  } finally {
    loading.value = false
  }
}

const applyStartOptions = (payload = {}, updatedAt = Date.now()) => {
  startUsers.value = payload.users?.length ? payload.users : [...demoStartUsers]
  startStations.value = payload.stations?.length ? payload.stations : getFallbackStationOptions()
  startForm.user_id = payload.default_user_id || startUsers.value[0]?.id || null
  startForm.station_id =
    payload.default_station_id ||
    startStations.value.find((item) => Number(item.status) === 0)?.id ||
    startStations.value[0]?.id ||
    null
  startChargers.value = (payload.chargers || []).filter((item) => Number(item.status) === 0)
  startForm.charger_id = startChargers.value[0]?.id || null
  if (!cacheLabel.value) {
    cacheLabel.value = formatCacheLabel(updatedAt)
  }
}

const loadChargersByStation = async (stationId) => {
  if (!stationId) {
    startChargers.value = []
    startForm.charger_id = null
    return
  }

  try {
    const { data } = await fetchStationChargers(stationId)
    startChargers.value = mergeChargersWithLocal(stationId, data?.data || []).filter((item) => Number(item.status) === 0)
    startForm.charger_id = startChargers.value[0]?.id || null
  } catch (error) {
    startChargers.value = mergeChargersWithLocal(stationId, []).filter((item) => Number(item.status) === 0)
    startForm.charger_id = startChargers.value[0]?.id || null
  }
}

const loadStartOptions = async ({ background = false } = {}) => {
  const cached = getRequestCache(startCacheKey.value, { ttl: CACHE_TTL, allowStale: true })
  if (cached) {
    applyStartOptions(cached.value, cached.updatedAt)
    if (!startForm.charger_id) {
      await loadChargersByStation(startForm.station_id)
    }
  }

  startOptionsLoading.value = !cached || !background
  try {
    const { data } = await fetchOperatorOrderStartOptions()
    const payload = data?.data || {}
    applyStartOptions(payload, Date.now())
    setRequestCache(startCacheKey.value, payload)
    if (!payload.chargers?.length) {
      await loadChargersByStation(startForm.station_id)
    }
  } catch (error) {
    if (!cached) {
      applyStartOptions({
        users: [...demoStartUsers],
        stations: getFallbackStationOptions(),
      })
      await loadChargersByStation(startForm.station_id)
    }
  } finally {
    startOptionsLoading.value = false
  }
}

const openStartDialog = (mode) => {
  startMode.value = mode
  startForm.source_type = mode === 'manual_demo' ? 'manual_demo' : 'qr_code'
  startDialogVisible.value = true
  loadStartOptions({ background: true })
}

const submitStartOrder = async () => {
  const user = startUsers.value.find((item) => String(item.id) === String(startForm.user_id))
  const station = startStations.value.find((item) => String(item.id) === String(startForm.station_id))
  const charger = startChargers.value.find((item) => String(item.id) === String(startForm.charger_id))

  if (!station || !charger) {
    ElMessage.warning('请选择已审核电站和空闲电桩')
    return
  }

  startLoading.value = true
  try {
    const { data } = await startDemoOrder({
      user_id: startForm.user_id,
      station_id: startForm.station_id,
      charger_id: startForm.charger_id,
      source_type: startForm.source_type,
    })
    ElMessage.success(data?.message || '演示订单创建成功')
  } catch (error) {
    startLocalDemoOrder({
      station,
      charger,
      user: user || demoStartUsers[0],
      sourceType: startForm.source_type,
    })
    ElMessage.success('已切换到本地演示订单')
  } finally {
    startLoading.value = false
    startDialogVisible.value = false
    await loadOrders()
  }
}

const handleFinish = async (row) => {
  try {
    await ElMessageBox.confirm(`确认结束订单 ${row.order_no} 吗？`, '结束订单', { type: 'warning' })
  } catch {
    return
  }

  try {
    busyOrderId.value = row.id
    await finishDemoOrder(row.id)
    ElMessage.success('订单已结束并完成扣费')
  } catch (error) {
    finishLocalDemoOrder(row.id)
    ElMessage.success('订单已转入历史订单')
  } finally {
    busyOrderId.value = null
    await loadOrders()
  }
}

const handleMarkAbnormal = async (row) => {
  let reason = ''
  try {
    const result = await ElMessageBox.prompt('请输入异常原因', '标记异常', {
      inputPlaceholder: '例如：设备连接中断',
      inputValidator: (value) => (value && value.trim() ? true : '异常原因不能为空'),
    })
    reason = result.value.trim()
  } catch {
    return
  }

  try {
    busyOrderId.value = row.id
    await markDemoOrderAbnormal(row.id, { reason })
    ElMessage.success('订单已标记为异常')
  } catch (error) {
    markLocalDemoOrderAbnormal(row.id, reason || '会话异常结束')
    ElMessage.success('订单已转入异常订单')
  } finally {
    busyOrderId.value = null
    await loadOrders()
  }
}

watch(
  () => startForm.station_id,
  async (value, oldValue) => {
    if (value && value !== oldValue) {
      await loadChargersByStation(value)
    }
  },
)

watch(
  () => startMode.value,
  (mode) => {
    startForm.source_type = mode === 'manual_demo' ? 'manual_demo' : 'qr_code'
  },
)

onMounted(async () => {
  await loadOrders({ background: true })
  await loadStartOptions({ background: true })
})

onActivated(() => {
  if (shouldRefreshRequestCache(listCacheKey.value, CACHE_TTL)) {
    loadOrders({ background: true })
  }
  if (shouldRefreshRequestCache(startCacheKey.value, CACHE_TTL)) {
    loadStartOptions({ background: true })
  }
})
</script>

<template>
  <div class="page-shell realtime-page">
    <PageSectionHeader
      eyebrow="订单中心"
      title="实时订单"
      description="查看当前充电中的订单，并支持演示发起、结束和异常处理。"
      chip="实时监控"
    >
      <template #actions>
        <el-tag v-if="cacheLabel" type="info" effect="plain">{{ cacheLabel }}</el-tag>
        <el-button type="primary" :icon="Plus" @click="openStartDialog('manual_demo')">演示创建订单</el-button>
        <el-button type="primary" plain :icon="Tickets" @click="openStartDialog('qr_code')">扫码充电</el-button>
        <el-button :icon="RefreshRight" :loading="loading" @click="loadOrders()">刷新列表</el-button>
      </template>
    </PageSectionHeader>

    <section class="stats-grid stats-grid--realtime">
      <MetricCard v-for="item in stats" :key="item.label" v-bind="item" />
    </section>

    <section class="page-panel surface-card table-shell">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">订单列表</h3>
          <p class="panel-heading__desc">共 {{ total }} 条记录。</p>
        </div>
      </div>
      <TableSkeletonBlock v-if="loading && !tableReady" :rows="6" :columns="8" />

      <el-table v-else-if="orders.length" :data="orders" v-loading="loading" stripe>
        <el-table-column prop="order_no" label="订单编号" min-width="190" />
        <el-table-column label="用户" min-width="150">
          <template #default="{ row }">
            <div class="cell-stack">
              <strong>{{ row.user_nickname }}</strong>
              <span>{{ row.user_phone }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="source_type_text" label="订单来源" width="120" align="center" />
        <el-table-column prop="start_time" label="开始时间" width="170" />
        <el-table-column prop="station_name" label="电站" min-width="170" />
        <el-table-column prop="charger_name" label="电桩" min-width="160" />
        <el-table-column label="电量(kWh)" width="110" align="right">
          <template #default="{ row }">{{ Number(row.charge_amount || 0).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="总费用" width="110" align="right">
          <template #default="{ row }">{{ formatMoney(row.total_amount) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="router.push(`/operator/orders/detail/${row.id}`)">查看详情</el-button>
            <el-button link type="success" :loading="busyOrderId === row.id" @click="handleFinish(row)">结束订单</el-button>
            <el-button link type="danger" :loading="busyOrderId === row.id" @click="handleMarkAbnormal(row)">标记异常</el-button>
          </template>
        </el-table-column>
      </el-table>

      <EmptyStateBlock v-else-if="!loading" title="暂无实时订单" description="当前没有处于充电中的订单。" />
    </section>

    <el-dialog v-model="startDialogVisible" width="620px" :title="sourceTypeLabel">
      <el-form label-width="96px" v-loading="startOptionsLoading">
        <el-form-item label="用户">
          <el-select v-model="startForm.user_id" style="width: 100%">
            <el-option v-for="item in startUsers" :key="item.id" :label="`${item.nickname} / ${item.phone}`" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="电站">
          <el-select v-model="startForm.station_id" style="width: 100%">
            <el-option v-for="item in manualStations" :key="item.id" :label="`${item.station_name} / ${item.status_text}`" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="电桩">
          <el-select v-model="startForm.charger_id" style="width: 100%">
            <el-option v-for="item in startChargers" :key="item.id" :label="`${item.charger_name} / ${item.type} / ${item.power_kw}kW`" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="订单来源">
          <el-tag type="primary">{{ startMode === 'manual_demo' ? '演示发起' : '扫码充电' }}</el-tag>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="startDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="startLoading" @click="submitStartOrder">确认发起</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.stats-grid--realtime {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.cell-stack {
  display: grid;
  gap: 4px;
}

.cell-stack span {
  color: var(--color-text-2);
}

@media (max-width: 1280px) {
  .stats-grid--realtime {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .stats-grid--realtime {
    grid-template-columns: 1fr;
  }
}
</style>
