<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { fetchOverviewSummary, fetchRealtimeOrders } from '../api/overview'

const loading = ref(false)
const summary = ref({
  today_orders: 0,
  today_orders_change: 0,
  today_revenue: 0,
  today_revenue_change: 0,
  online_piles: 0,
  total_piles: 0,
  pile_availability: 0,
  active_users: 0,
  new_users_month: 0,
})

const realtimeOrders = ref([])

const loadData = async () => {
  loading.value = true
  try {
    const [summaryRes, ordersRes] = await Promise.all([
      fetchOverviewSummary(),
      fetchRealtimeOrders(),
    ])

    summary.value = summaryRes.data
    realtimeOrders.value = ordersRes.data
  } catch (error) {
    console.error(error)
    ElMessage.error('加载概览数据失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="dashboard-root">
    <el-row :gutter="16" class="cards-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="card-title">今日订单</div>
          <div class="card-value">
            {{ summary.today_orders }}
          </div>
          <div class="card-sub">
            <span class="card-trend positive">+{{ summary.today_orders_change }}% 较昨日</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="card-title">今日收益</div>
          <div class="card-value">
            ¥{{ summary.today_revenue.toLocaleString() }}
          </div>
          <div class="card-sub">
            <span class="card-trend positive">+{{ summary.today_revenue_change }}% 较昨日</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="card-title">在线电桩</div>
          <div class="card-value">
            {{ summary.online_piles }}/{{ summary.total_piles }}
          </div>
          <div class="card-sub">
            可用率 {{ summary.pile_availability }}%
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="card-title">活跃用户</div>
          <div class="card-value">
            {{ summary.active_users.toLocaleString() }}
          </div>
          <div class="card-sub">
            本月新增 {{ summary.new_users_month }}
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="charts-row">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>订单趋势</span>
              <span class="card-header-sub">近 6 个月订单数量统计（预留图表区域）</span>
            </div>
          </template>
          <div class="chart-placeholder">此处预留折线图 / 柱状图组件</div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>收益趋势</span>
              <span class="card-header-sub">近 6 个月收益统计（预留图表区域）</span>
            </div>
          </template>
          <div class="chart-placeholder">此处预留收益趋势图表组件</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card
      v-loading="loading"
      shadow="hover"
      class="realtime-card"
    >
      <template #header>
        <div class="card-header">
          <span>实时充电订单</span>
          <span class="card-header-sub">当前正在进行的充电订单</span>
        </div>
      </template>

      <el-table
        :data="realtimeOrders"
        border
        style="width: 100%"
      >
        <el-table-column prop="user_name" label="用户" width="120" />
        <el-table-column prop="station_name" label="充电站" min-width="200" />
        <el-table-column prop="charged_kwh" label="已充电量 (kWh)" width="150" />
        <el-table-column
          prop="status"
          label="状态"
          width="120"
        >
          <template #default="{ row }">
            <el-tag type="success" v-if="row.status === 'charging'">充电中</el-tag>
            <el-tag v-else>—</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.dashboard-root {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.cards-row {
  margin-bottom: 8px;
}

.card-title {
  font-size: 14px;
  color: #909399;
  margin-bottom: 4px;
}

.card-value {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 4px;
}

.card-sub {
  font-size: 12px;
  color: #909399;
}

.card-trend.positive {
  color: #67c23a;
}

.charts-row {
  margin-bottom: 8px;
}

.card-header {
  display: flex;
  flex-direction: column;
}

.card-header-sub {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.chart-placeholder {
  height: 260px;
  border-radius: 8px;
  border: 1px dashed #dcdfe6;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
  font-size: 13px;
}

.realtime-card {
  margin-top: 4px;
}
</style>

