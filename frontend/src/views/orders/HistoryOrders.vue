<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, Search, Money, Tickets, DataAnalysis, Histogram } from '@element-plus/icons-vue'
import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import EmptyStateBlock from '../../components/console/EmptyStateBlock.vue'
import { ROLES, getStoredOperatorId } from '../../config/permissions'
import { useOrderStore } from '../../stores/order'
import type { Order, OrderStatus } from '../../types/order'

interface FilterForm {
  orderNo: string
  keyword: string
  stationName: string
  status: '' | OrderStatus
}

const route = useRoute()
const router = useRouter()
const orderStore = useOrderStore()

const isAdmin = computed(() => route.meta?.role === ROLES.ADMIN)
const scope = computed(() => ({
  role: isAdmin.value ? ROLES.ADMIN : ROLES.OPERATOR,
  operatorId: getStoredOperatorId(),
}))

const loading = ref(false)
const allOrders = ref<Order[]>([])
const currentPage = ref(1)
const pageSize = ref(10)

const searchForm = reactive<FilterForm>({
  orderNo: '',
  keyword: '',
  stationName: '',
  status: '',
})

const appliedFilters = reactive<FilterForm>({
  orderNo: '',
  keyword: '',
  stationName: '',
  status: '',
})

const statusOptions = computed(() =>
  isAdmin.value
    ? [
        { label: '充电中', value: 'charging' },
        { label: '已完成', value: 'completed' },
        { label: '异常', value: 'abnormal' },
      ]
    : [{ label: '已完成', value: 'completed' }],
)

const stationOptions = computed(() => {
  const names = Array.from(new Set(allOrders.value.map((item) => item.stationName)))
  return names.filter(Boolean)
})

const filteredOrders = computed(() => {
  const orderNoKw = appliedFilters.orderNo.trim().toLowerCase()
  const keyword = appliedFilters.keyword.trim().toLowerCase()
  const station = appliedFilters.stationName
  const status = appliedFilters.status

  return allOrders.value.filter((order) => {
    const orderNoOk = !orderNoKw || order.orderNo.toLowerCase().includes(orderNoKw)
    const keywordOk =
      !keyword ||
      order.phone.toLowerCase().includes(keyword) ||
      order.userName.toLowerCase().includes(keyword) ||
      (isAdmin.value && order.operatorName.toLowerCase().includes(keyword))
    const stationOk = !station || order.stationName === station
    const statusOk = !status || order.status === status

    return orderNoOk && keywordOk && stationOk && statusOk
  })
})

const total = computed(() => filteredOrders.value.length)

const tableData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredOrders.value.slice(start, start + pageSize.value)
})

const summaryCards = computed(() => {
  const totalRevenue = filteredOrders.value.reduce((sum, item) => sum + Number(item.totalAmount || 0), 0)
  const totalPower = filteredOrders.value.reduce((sum, item) => sum + Number(item.chargeAmount || 0), 0)
  const avgAmount = filteredOrders.value.length ? totalRevenue / filteredOrders.value.length : 0
  const avgDuration = filteredOrders.value.length
    ? filteredOrders.value.reduce((sum, item) => sum + Number(item.chargeDuration || 0), 0) / filteredOrders.value.length
    : 0

  return [
    {
      label: '订单总数',
      value: filteredOrders.value.length,
      suffix: ' 单',
      trend: '当前筛选结果',
      trendLabel: '用于对账与复盘',
      tone: 'primary',
      icon: Tickets,
    },
    {
      label: '累计订单金额',
      value: totalRevenue.toFixed(2),
      prefix: '¥',
      trend: '总收入汇总',
      trendLabel: '按已筛选订单累计',
      tone: 'success',
      icon: Money,
    },
    {
      label: '累计充电量',
      value: totalPower.toFixed(2),
      suffix: ' kWh',
      trend: '能耗规模',
      trendLabel: '用于运营分析',
      tone: 'info',
      icon: DataAnalysis,
    },
    {
      label: '平均客单价',
      value: avgAmount.toFixed(2),
      prefix: '¥',
      trend: `平均时长 ${Math.round(avgDuration)} 分钟`,
      trendLabel: '反映订单效率',
      tone: 'warning',
      icon: Histogram,
    },
  ]
})

const formatMoney = (value: number): string =>
  `¥${Number(value || 0).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`

const maskPhone = (phone: string): string => {
  if (!phone || phone.length < 7) return phone
  return `${phone.slice(0, 3)}****${phone.slice(-4)}`
}

const statusTag = (status: OrderStatus): { type: 'success' | 'warning' | 'danger'; text: string } => {
  if (status === 'charging') return { type: 'warning', text: '充电中' }
  if (status === 'abnormal') return { type: 'danger', text: '异常' }
  return { type: 'success', text: '已完成' }
}

const loadOrders = async () => {
  loading.value = true
  try {
    await new Promise((resolve) => {
      window.setTimeout(resolve, 120)
    })
    allOrders.value = isAdmin.value
      ? orderStore.getAllOrders(scope.value)
      : orderStore.getHistoryOrders(scope.value)
  } finally {
    loading.value = false
  }
}

const handleSearch = async () => {
  appliedFilters.orderNo = searchForm.orderNo
  appliedFilters.keyword = searchForm.keyword
  appliedFilters.stationName = searchForm.stationName
  appliedFilters.status = searchForm.status
  currentPage.value = 1
  await loadOrders()
}

const handleReset = async () => {
  searchForm.orderNo = ''
  searchForm.keyword = ''
  searchForm.stationName = ''
  searchForm.status = ''

  appliedFilters.orderNo = ''
  appliedFilters.keyword = ''
  appliedFilters.stationName = ''
  appliedFilters.status = ''
  currentPage.value = 1

  await loadOrders()
}

const handleSizeChange = (val: number): void => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val: number): void => {
  currentPage.value = val
}

const openDetail = (id: string): void => {
  const path = isAdmin.value ? `/admin/orders/detail/${id}` : `/operator/orders/detail/${id}`
  router.push(path)
}

onMounted(async () => {
  await loadOrders()
  ElMessage.success(isAdmin.value ? '全局历史订单数据已加载' : '历史订单已加载')
})
</script>

<template>
  <div class="page-shell history-orders-page">
    <PageSectionHeader
      eyebrow="History Orders"
      :title="isAdmin ? '历史订单监管' : '历史订单查询'"
      :description="isAdmin ? '按全平台视角查询历史订单并支持风险复盘。' : '按本机构视角查询历史订单并进行收益复盘。'"
      :chip="isAdmin ? '管理员订单视角' : '运营商订单视角'"
    >
      <template #actions>
        <el-button type="primary" :icon="Search" :loading="loading" @click="handleSearch">查询</el-button>
        <el-button :icon="Refresh" :disabled="loading" @click="handleReset">重置</el-button>
      </template>
    </PageSectionHeader>

    <section class="stats-grid stats-grid--history">
      <MetricCard
        v-for="item in summaryCards"
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
          <p class="panel-heading__desc">支持按订单号、关键词、场站和状态筛选。</p>
        </div>
      </div>

      <el-form :model="searchForm" class="filter-form" label-width="auto">
        <div class="filter-row">
          <el-form-item label="订单号" class="form-item">
            <el-input v-model="searchForm.orderNo" placeholder="支持模糊查询" clearable style="width: 210px" />
          </el-form-item>
          <el-form-item :label="isAdmin ? '手机号/用户/运营商' : '手机号/用户名'" class="form-item">
            <el-input v-model="searchForm.keyword" placeholder="支持手机号、用户名关键词" clearable style="width: 220px" />
          </el-form-item>
          <el-form-item label="场站" class="form-item">
            <el-select v-model="searchForm.stationName" placeholder="全部场站" clearable style="width: 200px">
              <el-option v-for="s in stationOptions" :key="s" :label="s" :value="s" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态" class="form-item">
            <el-select v-model="searchForm.status" placeholder="全部状态" clearable style="width: 150px">
              <el-option v-for="option in statusOptions" :key="option.value" :label="option.label" :value="option.value" />
            </el-select>
          </el-form-item>
        </div>
      </el-form>
    </section>

    <section class="page-panel surface-card table-shell">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">历史订单列表</h3>
          <p class="panel-heading__desc">共 {{ total }} 条记录，支持分页查看详情。</p>
        </div>
      </div>

      <el-table
        v-if="tableData.length"
        :data="tableData"
        stripe
        highlight-current-row
        v-loading="loading"
        element-loading-text="加载中..."
      >
        <el-table-column prop="orderNo" label="订单编号" width="190" show-overflow-tooltip />
        <el-table-column prop="startTime" label="开始时间" width="170" />
        <el-table-column prop="endTime" label="结束时间" width="170" />
        <el-table-column label="用户" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <span>{{ row.userName }}（{{ maskPhone(row.phone) }}）</span>
          </template>
        </el-table-column>
        <el-table-column v-if="isAdmin" prop="operatorName" label="运营商" min-width="180" show-overflow-tooltip />
        <el-table-column prop="stationName" label="所属场站" min-width="180" show-overflow-tooltip />
        <el-table-column prop="chargeAmount" label="充电量(kWh)" width="120" align="right">
          <template #default="{ row }">
            <span class="num">{{ Number(row.chargeAmount).toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="totalAmount" label="订单金额" width="140" align="right">
          <template #default="{ row }">
            <span class="money">{{ formatMoney(row.totalAmount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status).type">{{ statusTag(row.status).text }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right" align="center">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openDetail(row.id)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <EmptyStateBlock
        v-else-if="!loading"
        title="暂无历史订单"
        description="当前筛选条件下无数据，建议调整筛选后重试。"
      />

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </section>
  </div>
</template>

<style scoped>
.history-orders-page {
  padding-bottom: 8px;
}

.stats-grid--history {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.filter-form {
  width: 100%;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.form-item {
  margin-bottom: 0;
}

.num {
  font-variant-numeric: tabular-nums;
}

.money {
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: #303133;
}

.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
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
