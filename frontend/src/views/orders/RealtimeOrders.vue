<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DataAnalysis, Lightning, Money, RefreshRight } from '@element-plus/icons-vue'

import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import EmptyStateBlock from '../../components/console/EmptyStateBlock.vue'
import {
  fetchOperatorRealtimeOrders,
  finishOperatorOrder,
  markOperatorOrderAbnormal,
  startDemoCharging,
} from '../../api/operator'

const router = useRouter()
const loading = ref(false)
const actionLoading = ref(false)
const orders = ref([])

const formatMoney = (value) => `¥${Number(value || 0).toFixed(2)}`

const stats = computed(() => {
  const totalCount = orders.value.length
  const totalCharge = orders.value.reduce((sum, item) => sum + Number(item.charge_amount || 0), 0)
  const totalEleFee = orders.value.reduce((sum, item) => sum + Number(item.electricity_fee || 0), 0)
  const totalServiceFee = orders.value.reduce((sum, item) => sum + Number(item.service_fee || 0), 0)

  return [
    {
      label: '实时订单',
      value: totalCount,
      suffix: ' 单',
      trend: '当前充电会话',
      trendLabel: '支持实时状态演示',
      tone: 'primary',
      icon: Lightning,
    },
    {
      label: '实时电量',
      value: totalCharge.toFixed(2),
      suffix: ' kWh',
      trend: '在充订单累计',
      trendLabel: '用于展示实时业务量',
      tone: 'success',
      icon: DataAnalysis,
    },
    {
      label: '实时电费',
      value: totalEleFee.toFixed(2),
      prefix: '¥',
      trend: '电费累计',
      trendLabel: '结束时自动结算',
      tone: 'warning',
      icon: Money,
    },
    {
      label: '实时服务费',
      value: totalServiceFee.toFixed(2),
      prefix: '¥',
      trend: '服务费累计',
      trendLabel: '总费用 = 电费 + 服务费',
      tone: 'info',
      icon: RefreshRight,
    },
  ]
})

const loadOrders = async () => {
  loading.value = true
  try {
    const { data } = await fetchOperatorRealtimeOrders()
    orders.value = data.data || []
  } catch (error) {
    console.error(error)
    ElMessage.error('实时订单加载失败')
  } finally {
    loading.value = false
  }
}

const handleDemoStart = async () => {
  actionLoading.value = true
  try {
    const { data } = await startDemoCharging()
    ElMessage.success(data.message || '已创建实时订单')
    await loadOrders()
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.response?.data?.message || '模拟开始充电失败')
  } finally {
    actionLoading.value = false
  }
}

const handleFinish = async (row) => {
  try {
    await ElMessageBox.confirm(`确认结束订单 ${row.order_no} 吗？`, '结束充电', {
      type: 'warning',
      confirmButtonText: '确认结束',
      cancelButtonText: '取消',
    })
    const { data } = await finishOperatorOrder(row.id)
    ElMessage.success(data.message || '订单已完成')
    await loadOrders()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
      ElMessage.error(error?.response?.data?.message || '结束充电失败')
    }
  }
}

const handleMarkAbnormal = async (row) => {
  try {
    const result = await ElMessageBox.prompt('请输入异常原因', '标记异常', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      inputPlaceholder: '例如：充电枪中途断连',
      inputValidator: (value) => (value && value.trim() ? true : '异常原因不能为空'),
    })
    const { data } = await markOperatorOrderAbnormal(row.id, result.value.trim())
    ElMessage.success(data.message || '订单已转入异常订单')
    await loadOrders()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
      ElMessage.error(error?.response?.data?.message || '标记异常失败')
    }
  }
}

const openDetail = (row) => {
  router.push(`/operator/orders/detail/${row.id}`)
}

onMounted(loadOrders)
</script>

<template>
  <div class="page-shell realtime-page">
    <PageSectionHeader
      eyebrow="Realtime Orders"
      title="实时订单"
      description="支持模拟开始充电、结束充电和标记异常，形成实时订单到历史订单、异常订单的完整流转闭环。"
      chip="运营商订单管理"
    >
      <template #actions>
        <el-button type="primary" :loading="actionLoading" @click="handleDemoStart">模拟开始充电</el-button>
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
          <h3 class="panel-heading__title">实时订单列表</h3>
          <p class="panel-heading__desc">操作后列表会自动刷新，已完成订单进入历史订单，异常订单进入异常订单池。</p>
        </div>
      </div>

      <el-table v-if="orders.length" :data="orders" v-loading="loading" stripe>
        <el-table-column prop="order_no" label="订单编号" min-width="190" show-overflow-tooltip />
        <el-table-column prop="user_phone" label="用户账号" width="130" />
        <el-table-column prop="user_nickname" label="昵称" width="120" show-overflow-tooltip />
        <el-table-column prop="vin" label="VIN" min-width="170" show-overflow-tooltip />
        <el-table-column prop="start_time" label="开始时间" width="170" />
        <el-table-column prop="station_name" label="电站" min-width="170" show-overflow-tooltip />
        <el-table-column prop="charger_name" label="电桩" min-width="160" show-overflow-tooltip />
        <el-table-column prop="charge_amount" label="电量(kWh)" width="110" align="right">
          <template #default="{ row }">{{ Number(row.charge_amount).toFixed(2) }}</template>
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
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">查看详情</el-button>
            <el-button link type="success" @click="handleFinish(row)">结束充电</el-button>
            <el-button link type="danger" @click="handleMarkAbnormal(row)">标记异常</el-button>
          </template>
        </el-table-column>
      </el-table>

      <EmptyStateBlock
        v-else-if="!loading"
        title="当前暂无实时订单"
        description="点击“模拟开始充电”即可创建一条充电中的实时订单。"
      />
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
