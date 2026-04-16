<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DataAnalysis, Lightning, Money, RefreshRight } from '@element-plus/icons-vue'

import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import EmptyStateBlock from '../../components/console/EmptyStateBlock.vue'
import {
  fetchOperatorRealtimeOrders,
  forceStopOperatorOrder,
  markOperatorOrderAbnormal,
} from '../../api/operator'

const router = useRouter()
const loading = ref(false)
const errorMessage = ref('')
const orders = ref([])
const total = ref(0)
const busyOrderId = ref(null)

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

const formatMoney = (value) => `¥${Number(value || 0).toFixed(2)}`

const stats = computed(() => [
  {
    label: '实时订单',
    value: summary.total_count,
    suffix: ' 单',
    trend: '当前充电中的订单数量',
    trendLabel: '按实时状态持续更新',
    tone: 'primary',
    icon: Lightning,
  },
  {
    label: '实时电量',
    value: Number(summary.total_charge_amount || 0).toFixed(2),
    suffix: ' kWh',
    trend: '在充订单累计电量',
    trendLabel: '按在充订单汇总',
    tone: 'success',
    icon: DataAnalysis,
  },
  {
    label: '实时电费',
    value: Number(summary.total_ele_fee || 0).toFixed(2),
    prefix: '¥',
    trend: '当前电费汇总',
    trendLabel: '按在充订单实时计算',
    tone: 'warning',
    icon: Money,
  },
  {
    label: '实时服务费',
    value: Number(summary.total_service_fee || 0).toFixed(2),
    prefix: '¥',
    trend: '当前服务费汇总',
    trendLabel: '与电费合并计入订单总费用',
    tone: 'info',
    icon: RefreshRight,
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
    errorMessage.value = error?.response?.data?.message || error?.response?.data?.detail || '实时订单加载失败，请稍后重试。'
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

const handleForceStop = async (row) => {
  try {
    await ElMessageBox.confirm(`确认强制停止订单 ${row.order_no} 吗？`, '强制停止', {
      type: 'warning',
      confirmButtonText: '确认',
      cancelButtonText: '取消',
    })
    busyOrderId.value = row.id
    const { data } = await forceStopOperatorOrder(row.id)
    ElMessage.success(data.message || '订单已强制停止')
    await refreshAfterMutation()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
      ElMessage.error(error?.response?.data?.message || error?.response?.data?.detail || '强制停止失败')
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
      inputPlaceholder: '例如：设备通讯中断',
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

onMounted(loadOrders)
</script>

<template>
  <div class="page-shell realtime-page">
    <PageSectionHeader
      eyebrow="订单中心"
      title="实时订单"
      description="查看正在充电的订单，并进行结束充电或异常处理。"
      chip="实时监控"
    >
      <template #actions>
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
        <el-table-column prop="user_phone" label="用户账号" width="130" />
        <el-table-column prop="user_nickname" label="昵称" width="120" show-overflow-tooltip />
        <el-table-column prop="vin" label="VIN" min-width="170" show-overflow-tooltip />
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
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">查看详情</el-button>
            <el-button link type="warning" :loading="busyOrderId === row.id" @click="handleForceStop(row)">强制停止</el-button>
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
