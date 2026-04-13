<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { DataAnalysis, Money, RefreshRight, Tickets } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import EmptyStateBlock from '../../components/console/EmptyStateBlock.vue'
import { fetchAdminOrders } from '../../api/admin'
import { fetchOperatorHistoryOrders } from '../../api/operator'
import { ROLES } from '../../config/permissions'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const orders = ref([])

const filters = reactive({
  keyword: '',
  station: '',
})

const formatMoney = (value) => `¥${Number(value || 0).toFixed(2)}`
const isAdmin = computed(() => route.meta?.role === ROLES.ADMIN)

const stationOptions = computed(() => [...new Set(orders.value.map((item) => item.station_name).filter(Boolean))])

const filteredOrders = computed(() => {
  const keyword = filters.keyword.trim().toLowerCase()
  return orders.value.filter((item) => {
    const matchKeyword =
      !keyword ||
      [item.order_no, item.user_phone, item.user_nickname, item.vin, item.charger_name]
        .filter(Boolean)
        .some((field) => String(field).toLowerCase().includes(keyword))
    const matchStation = !filters.station || filters.station === item.station_name
    return matchKeyword && matchStation
  })
})

const stats = computed(() => {
  const totalCount = filteredOrders.value.length
  const totalCharge = filteredOrders.value.reduce((sum, item) => sum + Number(item.charge_amount || 0), 0)
  const totalRevenue = filteredOrders.value.reduce((sum, item) => sum + Number(item.total_amount || 0), 0)
  const totalServiceFee = filteredOrders.value.reduce((sum, item) => sum + Number(item.service_fee || 0), 0)

  return [
    {
      label: '历史订单',
      value: totalCount,
      suffix: ' 单',
      trend: '已完成订单',
      trendLabel: '用于展示业务沉淀',
      tone: 'primary',
      icon: Tickets,
    },
    {
      label: '累计电量',
      value: totalCharge.toFixed(2),
      suffix: ' kWh',
      trend: '已完成充电量',
      trendLabel: '适合论文统计截图',
      tone: 'success',
      icon: DataAnalysis,
    },
    {
      label: '累计营收',
      value: totalRevenue.toFixed(2),
      prefix: '¥',
      trend: '订单总费用',
      trendLabel: '电费与服务费之和',
      tone: 'warning',
      icon: Money,
    },
    {
      label: '累计服务费',
      value: totalServiceFee.toFixed(2),
      prefix: '¥',
      trend: '服务费累计',
      trendLabel: '便于运营复盘',
      tone: 'info',
      icon: RefreshRight,
    },
  ]
})

const loadOrders = async () => {
  loading.value = true
  try {
    const response = isAdmin.value ? await fetchAdminOrders() : await fetchOperatorHistoryOrders()
    const list = response.data.data || []
    orders.value = isAdmin.value ? list.filter((item) => Number(item.status) === 1) : list
  } catch (error) {
    console.error(error)
    ElMessage.error('历史订单加载失败')
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.keyword = ''
  filters.station = ''
}

const openDetail = (row) => {
  router.push(isAdmin.value ? `/admin/orders/detail/${row.id}` : `/operator/orders/detail/${row.id}`)
}

onMounted(loadOrders)
</script>

<template>
  <div class="page-shell history-page">
    <PageSectionHeader
      eyebrow="History Orders"
      :title="isAdmin ? '全局历史订单' : '历史订单'"
      :description="isAdmin ? '管理员查看全平台已完成订单。' : '查看已完成订单的电量、费用和时间信息，适合做论文成果页和订单复盘页。'"
      :chip="isAdmin ? '管理员订单管理' : '运营商订单管理'"
    >
      <template #actions>
        <el-button :icon="RefreshRight" :loading="loading" @click="loadOrders">刷新列表</el-button>
      </template>
    </PageSectionHeader>

    <section class="stats-grid stats-grid--history">
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

    <section class="page-panel surface-card">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">筛选条件</h3>
          <p class="panel-heading__desc">支持按订单号、用户、VIN 和电站筛选历史订单。</p>
        </div>
        <div class="toolbar-actions">
          <el-button @click="resetFilters">重置</el-button>
        </div>
      </div>

      <div class="filter-row">
        <el-input v-model="filters.keyword" clearable placeholder="订单号 / 用户账号 / 昵称 / VIN" style="width: 320px" />
        <el-select v-model="filters.station" clearable placeholder="选择电站" style="width: 220px">
          <el-option v-for="item in stationOptions" :key="item" :label="item" :value="item" />
        </el-select>
      </div>
    </section>

    <section class="page-panel surface-card table-shell">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">历史订单列表</h3>
          <p class="panel-heading__desc">共 {{ filteredOrders.length }} 条记录，支持跳转详情页查看完整订单信息。</p>
        </div>
      </div>

      <el-table v-if="filteredOrders.length" :data="filteredOrders" v-loading="loading" stripe>
        <el-table-column prop="order_no" label="订单编号" min-width="190" show-overflow-tooltip />
        <el-table-column prop="user_phone" label="用户账号" width="130" />
        <el-table-column prop="user_nickname" label="昵称" width="120" />
        <el-table-column prop="vin" label="VIN" min-width="170" show-overflow-tooltip />
        <el-table-column label="起止时间" min-width="260">
          <template #default="{ row }">
            <div class="time-range">
              <span>{{ row.start_time }}</span>
              <span>{{ row.end_time || '-' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="charge_amount" label="电量(kWh)" width="110" align="right">
          <template #default="{ row }">{{ Number(row.charge_amount).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="electricity_fee" label="电费" width="100" align="right">
          <template #default="{ row }">{{ formatMoney(row.electricity_fee) }}</template>
        </el-table-column>
        <el-table-column prop="service_fee" label="服务费" width="100" align="right">
          <template #default="{ row }">{{ formatMoney(row.service_fee) }}</template>
        </el-table-column>
        <el-table-column prop="total_amount" label="总费用" width="110" align="right">
          <template #default="{ row }">{{ formatMoney(row.total_amount) }}</template>
        </el-table-column>
        <el-table-column prop="station_name" label="电站" min-width="160" show-overflow-tooltip />
        <el-table-column prop="charger_name" label="电桩" min-width="160" show-overflow-tooltip />
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="success">{{ row.status_text }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <EmptyStateBlock
        v-else-if="!loading"
        title="暂无历史订单"
        description="当前还没有已完成订单，可以先在实时订单页模拟开始充电并结束订单。"
      />
    </section>
  </div>
</template>

<style scoped>
.history-page {
  padding-bottom: 8px;
}

.stats-grid--history {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.toolbar-actions {
  display: flex;
  gap: 10px;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.time-range {
  display: grid;
  gap: 4px;
}

.time-range span:last-child {
  color: var(--color-text-2);
}

@media (max-width: 1280px) {
  .stats-grid--history {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .stats-grid--history {
    grid-template-columns: 1fr;
  }
}
</style>
