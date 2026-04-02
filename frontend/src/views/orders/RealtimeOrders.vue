<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { VideoPlay, DataLine, Loading, WarningFilled, RefreshRight } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import EmptyStateBlock from '../../components/console/EmptyStateBlock.vue'
import { ROLES, getStoredOperatorId } from '../../config/permissions'
import { useOrderStore } from '../../stores/order'

const router = useRouter()
const orderStore = useOrderStore()

const scope = {
  role: ROLES.OPERATOR,
  operatorId: getStoredOperatorId(),
}

const loading = ref(true)
const tableData = ref(orderStore.getRealtimeOrders(scope))
let refreshTimer: number | null = null

const refreshRealtimeOrders = async () => {
  loading.value = true
  try {
    await new Promise((resolve) => {
      window.setTimeout(resolve, 120)
    })
    tableData.value = orderStore.getRealtimeOrders(scope)
  } finally {
    loading.value = false
  }
}

const stats = computed(() => ({
  active: tableData.value.length,
  totalPower: tableData.value.reduce((sum, item) => sum + Number(item.chargeAmount || 0), 0).toFixed(1),
  currentFee: tableData.value.reduce((sum, item) => sum + Number(item.totalAmount || 0), 0).toFixed(2),
  avgDuration: tableData.value.length
    ? Math.round(tableData.value.reduce((sum, item) => sum + Number(item.chargeDuration || 0), 0) / tableData.value.length)
    : 0,
}))

const statCards = computed(() => [
  {
    label: '当前充电中车辆',
    value: stats.value.active,
    suffix: ' 辆',
    trend: '实时在线订单',
    trendLabel: '每 30 秒自动刷新',
    tone: 'primary',
    icon: VideoPlay,
  },
  {
    label: '实时总输出电量',
    value: stats.value.totalPower,
    suffix: ' kWh',
    trend: '当前会话累计',
    trendLabel: '用于判断站点负载',
    tone: 'success',
    icon: DataLine,
  },
  {
    label: '当前预计总流水',
    value: stats.value.currentFee,
    prefix: '¥',
    trend: '实时金额估算',
    trendLabel: '按在充订单动态累计',
    tone: 'warning',
    icon: Loading,
  },
  {
    label: '平均充电时长',
    value: stats.value.avgDuration,
    suffix: ' 分钟',
    trend: '会话效率监控',
    trendLabel: '用于判断异常波动',
    tone: 'info',
    icon: WarningFilled,
  },
])

const handleForceStop = async (row: { id: string }) => {
  try {
    await ElMessageBox.confirm('确认强制停止该订单吗？', '强制停止', {
      confirmButtonText: '确认停止',
      cancelButtonText: '取消',
      type: 'warning',
    })
    const result = orderStore.finishOrder(row.id, scope)
    if (!result) {
      ElMessage.warning('仅本机构充电中订单可执行此操作')
      return
    }
    ElMessage.success('订单已结束并归档到历史订单')
    await refreshRealtimeOrders()
  } catch (error) {
    // cancel
  }
}

const handleMarkAbnormal = async (row: { id: string }) => {
  try {
    const { value } = await ElMessageBox.prompt('请输入异常原因', '标记异常', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      inputPlaceholder: '例如：充电枪中途断连',
      inputValidator: (val) => (val && val.trim().length > 0 ? true : '请填写异常原因'),
    })
    const result = orderStore.markOrderAbnormal(row.id, value, scope)
    if (!result) {
      ElMessage.warning('仅本机构充电中订单可执行此操作')
      return
    }
    ElMessage.success('订单已转入本机构异常订单')
    await refreshRealtimeOrders()
  } catch (error) {
    // cancel
  }
}

const openDetail = (id: string) => {
  router.push(`/operator/orders/detail/${id}`)
}

onMounted(() => {
  refreshRealtimeOrders()
  refreshTimer = window.setInterval(refreshRealtimeOrders, 30000)
})

onUnmounted(() => {
  if (refreshTimer) window.clearInterval(refreshTimer)
})
</script>

<template>
  <div class="page-shell realtime-orders-page">
    <PageSectionHeader
      eyebrow="Realtime Orders"
      title="实时订单监控"
      description="聚焦当前在充订单状态，支持异常标记与强制停止处理。"
      chip="运营商订单模块"
    >
      <template #actions>
        <div class="live-info">
          <span class="live-indicator"></span>
          <span>实时同步中（30s 刷新）</span>
        </div>
        <el-button plain @click="router.push('/operator/orders/abnormal')">异常订单</el-button>
        <el-button plain @click="router.push('/operator/orders/history')">历史订单</el-button>
        <el-button type="primary" :icon="RefreshRight" plain @click="refreshRealtimeOrders">手动刷新</el-button>
      </template>
    </PageSectionHeader>

    <section class="stats-grid stats-grid--realtime">
      <MetricCard
        v-for="item in statCards"
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
          <h3 class="panel-heading__title">本机构实时订单列表</h3>
          <p class="panel-heading__desc">展示实时电量进度与金额变化，便于值班人员快速处置。</p>
        </div>
      </div>

      <el-table :data="tableData" v-loading="loading" stripe v-if="tableData.length">
        <el-table-column prop="orderNo" label="订单编号" width="190">
          <template #default="scopeRow">
            <span class="order-no">{{ scopeRow.row.orderNo }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="chargerName" label="充电终端" width="160" />
        <el-table-column prop="phone" label="用户账号" width="120" />
        <el-table-column prop="startTime" label="开始时间" width="180" />
        <el-table-column label="已充时长" width="120" align="center">
          <template #default="scopeRow">
            <el-tag type="success" effect="plain">{{ scopeRow.row.chargeDuration }} 分钟</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="当前电量(实时)" min-width="220">
          <template #default="scopeRow">
            <div class="kwh-progress">
              <span>{{ scopeRow.row.chargeAmount }} kWh</span>
              <el-progress
                :percentage="Math.min(100, scopeRow.row.chargeAmount * 2)"
                :show-text="false"
                :stroke-width="8"
                striped
                striped-flow
              />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="totalAmount" label="当前金额" width="110" align="right">
          <template #default="scopeRow">
            <strong class="money">¥{{ Number(scopeRow.row.totalAmount).toFixed(2) }}</strong>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="scopeRow">
            <el-button link type="primary" size="small" @click="openDetail(scopeRow.row.id)">详情</el-button>
            <el-button link type="warning" size="small" @click="handleMarkAbnormal(scopeRow.row)">标记异常</el-button>
            <el-button link type="danger" size="small" @click="handleForceStop(scopeRow.row)">强制停止</el-button>
          </template>
        </el-table-column>
      </el-table>

      <EmptyStateBlock
        v-else-if="!loading"
        title="当前暂无实时订单"
        description="当前没有充电中的订单，会在有新会话时自动出现。"
      />
    </section>
  </div>
</template>

<style scoped>
.realtime-orders-page {
  padding-bottom: 8px;
}

.stats-grid--realtime {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.live-info {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-right: 6px;
  color: var(--color-text-2);
  font-size: 12px;
}

.live-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #67c23a;
  box-shadow: 0 0 8px #67c23a;
  animation: pulse 1.5s infinite;
}

.order-no {
  font-family: var(--font-family-mono);
  color: #2563eb;
}

.kwh-progress {
  display: grid;
  gap: 6px;
}

.kwh-progress span {
  color: var(--color-text-2);
  font-size: 12px;
}

.money {
  color: #ef4444;
}

@keyframes pulse {
  0% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(103, 194, 58, 0.7);
  }
  70% {
    transform: scale(1);
    box-shadow: 0 0 0 6px rgba(103, 194, 58, 0);
  }
  100% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(103, 194, 58, 0);
  }
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
