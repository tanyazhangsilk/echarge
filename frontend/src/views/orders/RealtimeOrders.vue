<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DataAnalysis, Lightning, Money, Plus, RefreshRight, Tickets } from '@element-plus/icons-vue'

import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import EmptyStateBlock from '../../components/console/EmptyStateBlock.vue'
import {
  fetchOperatorOrderStartOptions,
  fetchOperatorRealtimeOrders,
  fetchStationChargers,
  finishOperatorOrder,
  markOperatorOrderAbnormal,
  startDemoCharging,
} from '../../api/operator'

const router = useRouter()
const loading = ref(false)
const errorMessage = ref('')
const orders = ref([])
const total = ref(0)
const busyOrderId = ref(null)
const startDialogVisible = ref(false)
const startLoading = ref(false)
const startOptionsLoading = ref(false)
const startMode = ref('manual_demo')
const startUsers = ref([])
const startStations = ref([])
const startChargers = ref([])

const pagination = reactive({
  page: 1,
  pageSize: 10,
})

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

const manualStations = computed(() => startStations.value.filter((item) => item.status === 0))
const sourceTypeLabel = computed(() => (startMode.value === 'manual_demo' ? '手动模拟充电' : '扫码充电'))

const formatMoney = (value) => `¥${Number(value || 0).toFixed(2)}`

const stats = computed(() => [
  {
    label: '实时订单',
    value: summary.total_count,
    suffix: ' 单',
    trend: '当前仍在充电中的订单数量',
    trendLabel: '可从这里结束或转异常',
    tone: 'primary',
    icon: Lightning,
  },
  {
    label: '实时电量',
    value: Number(summary.total_charge_amount || 0).toFixed(2),
    suffix: ' kWh',
    trend: '在充订单累计电量',
    trendLabel: '用于跟踪当前会话规模',
    tone: 'success',
    icon: DataAnalysis,
  },
  {
    label: '实时电费',
    value: Number(summary.total_ele_fee || 0).toFixed(2),
    prefix: '¥',
    trend: '当前电费汇总',
    trendLabel: '按在充订单实时试算',
    tone: 'warning',
    icon: Money,
  },
  {
    label: '实时服务费',
    value: Number(summary.total_service_fee || 0).toFixed(2),
    prefix: '¥',
    trend: '当前服务费汇总',
    trendLabel: '与电费合并构成订单总额',
    tone: 'info',
    icon: Tickets,
  },
])

const loadOrders = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const { data } = await fetchOperatorRealtimeOrders({
      page: pagination.page,
      page_size: pagination.pageSize,
    })

    const payload = data.data || {}
    orders.value = payload.items || []
    total.value = Number(payload.total || 0)
    pagination.page = Number(payload.page || pagination.page)
    pagination.pageSize = Number(payload.page_size || pagination.pageSize)
    Object.assign(summary, payload.summary || {})
  } catch (error) {
    console.error(error)
    orders.value = []
    total.value = 0
    Object.assign(summary, {
      total_count: 0,
      total_charge_amount: 0,
      total_ele_fee: 0,
      total_service_fee: 0,
    })
    errorMessage.value = error?.response?.data?.message || error?.response?.data?.detail || '实时订单加载失败'
    ElMessage.error(errorMessage.value)
  } finally {
    loading.value = false
  }
}

const refreshAfterMutation = async () => {
  await loadOrders()
  if (!orders.value.length && pagination.page > 1) {
    pagination.page -= 1
    await loadOrders()
  }
}

const loadStartOptions = async () => {
  startOptionsLoading.value = true
  try {
    const { data } = await fetchOperatorOrderStartOptions()
    const payload = data.data || {}
    startUsers.value = payload.users || []
    startStations.value = payload.stations || []
    startForm.user_id = payload.default_user_id || startUsers.value[0]?.id || null
    const defaultApprovedStation = startStations.value.find((item) => item.status === 0)
    startForm.station_id = defaultApprovedStation?.id || payload.default_station_id || null
    startChargers.value = (payload.chargers || []).filter((item) => ![2, 3].includes(item.status))
    startForm.charger_id = startChargers.value[0]?.id || null
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.response?.data?.message || '启动充电选项加载失败')
  } finally {
    startOptionsLoading.value = false
  }
}

const openStartDialog = async (mode) => {
  startMode.value = mode
  startForm.source_type = mode === 'manual_demo' ? 'manual_demo' : 'qr_code'
  startDialogVisible.value = true
  await loadStartOptions()
}

const loadChargersByStation = async (stationId) => {
  if (!stationId) {
    startChargers.value = []
    startForm.charger_id = null
    return
  }
  try {
    const { data } = await fetchStationChargers(stationId)
    startChargers.value = (data.data || []).filter((item) => ![2, 3].includes(item.status))
    startForm.charger_id = startChargers.value[0]?.id || null
  } catch (error) {
    console.error(error)
    startChargers.value = []
    startForm.charger_id = null
    ElMessage.error(error?.response?.data?.message || '电桩选项加载失败')
  }
}

const submitStartOrder = async () => {
  if (!startForm.station_id) {
    ElMessage.warning('请选择电站')
    return
  }
  if (!startForm.charger_id) {
    ElMessage.warning('请选择电桩')
    return
  }

  startLoading.value = true
  try {
    const { data } = await startDemoCharging({
      user_id: startForm.user_id,
      station_id: startForm.station_id,
      charger_id: startForm.charger_id,
      source_type: startForm.source_type,
    })
    ElMessage.success(data.message || '实时订单已创建')
    startDialogVisible.value = false
    await refreshAfterMutation()
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.response?.data?.message || '发起充电失败')
  } finally {
    startLoading.value = false
  }
}

const handleFinish = async (row) => {
  try {
    await ElMessageBox.confirm(`确认结束订单 ${row.order_no} 吗？`, '结束充电', {
      type: 'warning',
      confirmButtonText: '确认',
      cancelButtonText: '取消',
    })
    busyOrderId.value = row.id
    const { data } = await finishOperatorOrder(row.id)
    ElMessage.success(data.message || '订单已完成')
    await refreshAfterMutation()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
      ElMessage.error(error?.response?.data?.message || error?.response?.data?.detail || '结束充电失败')
    }
  } finally {
    busyOrderId.value = null
  }
}

const handleMarkAbnormal = async (row) => {
  try {
    const result = await ElMessageBox.prompt('请输入异常原因', '标记异常', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      inputPlaceholder: '例如：设备通讯中断、枪头异常、会话未能正常结束',
      inputValidator: (value) => (value && value.trim() ? true : '异常原因不能为空'),
    })
    busyOrderId.value = row.id
    const { data } = await markOperatorOrderAbnormal(row.id, result.value.trim())
    ElMessage.success(data.message || '订单已转入异常订单')
    await refreshAfterMutation()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
      ElMessage.error(error?.response?.data?.message || error?.response?.data?.detail || '标记异常失败')
    }
  } finally {
    busyOrderId.value = null
  }
}

const openDetail = (row) => {
  router.push(`/operator/orders/detail/${row.id}`)
}

const handlePageChange = (page) => {
  pagination.page = page
  loadOrders()
}

const handleSizeChange = (size) => {
  pagination.page = 1
  pagination.pageSize = size
  loadOrders()
}

watch(
  () => startForm.station_id,
  (stationId, previous) => {
    if (stationId && stationId !== previous) {
      loadChargersByStation(stationId)
    }
  },
)

watch(
  () => startMode.value,
  (mode) => {
    startForm.source_type = mode === 'manual_demo' ? 'manual_demo' : 'qr_code'
  },
)

onMounted(loadOrders)
</script>

<template>
  <div class="page-shell realtime-page">
    <PageSectionHeader
      eyebrow="订单中心"
      title="实时订单"
      description="监控当前充电中的订单，并支持手动模拟、扫码占位、结束充电和异常处理。"
      chip="实时监控"
    >
      <template #actions>
        <el-button type="primary" :icon="Plus" @click="openStartDialog('manual_demo')">手动模拟充电</el-button>
        <el-button type="primary" plain :icon="Tickets" @click="openStartDialog('qr_code')">扫码充电</el-button>
        <el-button :icon="RefreshRight" :loading="loading" @click="loadOrders">刷新列表</el-button>
      </template>
    </PageSectionHeader>

    <section class="stats-grid stats-grid--realtime">
      <MetricCard
        v-for="item in stats"
        :key="item.label"
        :label="item.label"
        :value="item.value"
        :prefix="item.prefix"
        :suffix="item.suffix"
        :trend="item.trend"
        :trend-label="item.trendLabel"
        :tone="item.tone"
        :icon="item.icon"
      />
    </section>

    <section class="page-panel surface-card table-shell">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">订单列表</h3>
          <p class="panel-heading__desc">共 {{ total }} 条记录。</p>
        </div>
      </div>

      <el-alert
        v-if="errorMessage"
        :title="errorMessage"
        type="error"
        show-icon
        :closable="false"
        class="panel-alert"
      >
        <template #default>
          <el-button link type="primary" @click="loadOrders">重新获取</el-button>
        </template>
      </el-alert>

      <el-table v-if="orders.length" :data="orders" v-loading="loading" stripe>
        <el-table-column prop="order_no" label="订单编号" min-width="190" show-overflow-tooltip />
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
        <el-table-column prop="station_name" label="电站" min-width="170" show-overflow-tooltip />
        <el-table-column prop="charger_name" label="电桩" min-width="160" show-overflow-tooltip />
        <el-table-column prop="charge_amount" label="电量(kWh)" width="110" align="right">
          <template #default="{ row }">{{ Number(row.charge_amount || 0).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="electricity_fee" label="电费" width="100" align="right">
          <template #default="{ row }">{{ formatMoney(row.electricity_fee) }}</template>
        </el-table-column>
        <el-table-column prop="service_fee" label="服务费" width="100" align="right">
          <template #default="{ row }">{{ formatMoney(row.service_fee) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="warning">{{ row.status_text }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">查看详情</el-button>
            <el-button link type="success" :loading="busyOrderId === row.id" @click="handleFinish(row)">结束充电</el-button>
            <el-button link type="danger" :loading="busyOrderId === row.id" @click="handleMarkAbnormal(row)">标记异常</el-button>
          </template>
        </el-table-column>
      </el-table>

      <EmptyStateBlock
        v-else-if="!loading"
        title="暂无实时订单"
        description="当前没有处于充电中的订单。"
      />

      <div class="pager">
        <el-pagination
          :current-page="pagination.page"
          :page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </section>

    <el-dialog v-model="startDialogVisible" width="620px" :title="sourceTypeLabel">
      <el-form label-width="96px" v-loading="startOptionsLoading">
        <el-form-item label="用户">
          <el-select v-model="startForm.user_id" style="width: 100%">
            <el-option
              v-for="item in startUsers"
              :key="item.id"
              :label="`${item.nickname} · ${item.phone}`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="电站">
          <el-select v-model="startForm.station_id" style="width: 100%">
            <el-option
              v-for="item in manualStations"
              :key="item.id"
              :label="`${item.station_name} · ${item.status_text}`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="电桩">
          <el-select v-model="startForm.charger_id" style="width: 100%">
            <el-option
              v-for="item in startChargers"
              :key="item.id"
              :label="`${item.charger_name} · ${item.type} · ${item.power_kw}kW`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item v-if="startMode !== 'manual_demo'" label="接入来源">
          <el-radio-group v-model="startForm.source_type">
            <el-radio-button label="qr_code">扫码充电</el-radio-button>
            <el-radio-button label="mini_program">小程序</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-else label="订单来源">
          <el-tag type="primary">手动模拟</el-tag>
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
.realtime-page {
  padding-bottom: 8px;
}

.stats-grid--realtime {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.panel-alert {
  margin-bottom: 16px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
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
