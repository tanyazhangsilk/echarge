<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { DataAnalysis, Money, RefreshRight, Tickets } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import EmptyStateBlock from '../../components/console/EmptyStateBlock.vue'
import { fetchAdminOrders, fetchStationAudits } from '../../api/admin'
import { fetchOperatorHistoryOrders, fetchOperatorStations } from '../../api/operator'
import { ROLES } from '../../config/permissions'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const stationLoading = ref(false)
const errorMessage = ref('')
const orders = ref([])
const total = ref(0)
const stationOptions = ref([])

const pagination = reactive({
  page: 1,
  pageSize: 10,
})

const filters = reactive({
  keyword: '',
  stationId: '',
  dateRange: [],
})

const summary = reactive({
  total_count: 0,
  total_charge_amount: 0,
  total_amount: 0,
  total_service_fee: 0,
})

let searchTimer = null

const isAdmin = computed(() => route.meta?.role === ROLES.ADMIN)
const pageTitle = computed(() => (isAdmin.value ? '订单管理' : '历史订单'))
const pageChip = computed(() => (isAdmin.value ? '平台订单' : '订单中心'))

const formatMoney = (value) => `¥${Number(value || 0).toFixed(2)}`

const stats = computed(() => [
  {
    label: '历史订单',
    value: summary.total_count,
    suffix: ' 单',
    trend: '当前筛选条件下的完成订单',
    trendLabel: '统计结果来自服务端分页接口',
    tone: 'primary',
    icon: Tickets,
  },
  {
    label: '累计电量',
    value: Number(summary.total_charge_amount || 0).toFixed(2),
    suffix: ' kWh',
    trend: '已完成订单累计充电量',
    trendLabel: '按筛选条件实时汇总',
    tone: 'success',
    icon: DataAnalysis,
  },
  {
    label: '累计营收',
    value: Number(summary.total_amount || 0).toFixed(2),
    prefix: '¥',
    trend: '订单总费用汇总',
    trendLabel: '含电费与服务费',
    tone: 'warning',
    icon: Money,
  },
  {
    label: '累计服务费',
    value: Number(summary.total_service_fee || 0).toFixed(2),
    prefix: '¥',
    trend: '服务费汇总',
    trendLabel: '便于对账与复核',
    tone: 'info',
    icon: RefreshRight,
  },
])

const buildQueryParams = () => ({
  page: pagination.page,
  page_size: pagination.pageSize,
  keyword: filters.keyword.trim() || undefined,
  station_id: filters.stationId || undefined,
  start_date: filters.dateRange?.[0] || undefined,
  end_date: filters.dateRange?.[1] || undefined,
  status: isAdmin.value ? 1 : undefined,
})

const loadOrders = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const response = isAdmin.value
      ? await fetchAdminOrders(buildQueryParams())
      : await fetchOperatorHistoryOrders(buildQueryParams())

    const payload = response.data.data || {}
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
      total_amount: 0,
      total_service_fee: 0,
    })
    errorMessage.value = error?.response?.data?.message || '历史订单加载失败，请稍后重试。'
    ElMessage.error(errorMessage.value)
  } finally {
    loading.value = false
  }
}

const loadStationOptions = async () => {
  stationLoading.value = true
  try {
    if (isAdmin.value) {
      const { data } = await fetchStationAudits()
      stationOptions.value = (data.data || []).map((item) => ({
        label: item.station_name,
        value: item.id,
      }))
      return
    }

    const { data } = await fetchOperatorStations({ page: 1, page_size: 100 })
    stationOptions.value = (data.data?.items || []).map((item) => ({
      label: item.station_name,
      value: item.id,
    }))
  } catch (error) {
    console.error(error)
    stationOptions.value = []
  } finally {
    stationLoading.value = false
  }
}

const resetFilters = () => {
  filters.keyword = ''
  filters.stationId = ''
  filters.dateRange = []
}

const openDetail = (row) => {
  router.push(isAdmin.value ? `/admin/orders/detail/${row.id}` : `/operator/orders/detail/${row.id}`)
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
  () => [filters.keyword, filters.stationId, JSON.stringify(filters.dateRange)],
  () => {
    if (searchTimer) {
      clearTimeout(searchTimer)
    }
    searchTimer = setTimeout(() => {
      pagination.page = 1
      loadOrders()
    }, 300)
  },
)

onMounted(async () => {
  await Promise.all([loadOrders(), loadStationOptions()])
})

onBeforeUnmount(() => {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
})
</script>

<template>
  <div class="page-shell history-page">
    <PageSectionHeader
      eyebrow="订单中心"
      :title="pageTitle"
      description="查询已完成订单的时间、费用和结算信息。"
      :chip="pageChip"
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
          <p class="panel-heading__desc">支持按订单、用户、站点和时间范围查询。</p>
        </div>
        <div class="toolbar-actions">
          <el-button @click="resetFilters">重置</el-button>
        </div>
      </div>

      <div class="filter-row">
        <el-input v-model="filters.keyword" clearable placeholder="订单号 / 用户账号 / 昵称 / VIN" style="width: 320px" />
        <el-select
          v-model="filters.stationId"
          clearable
          filterable
          :loading="stationLoading"
          placeholder="选择电站"
          style="width: 220px"
        >
          <el-option v-for="item in stationOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-date-picker
          v-model="filters.dateRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
        />
      </div>
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
          <template #default="{ row }">{{ Number(row.charge_amount || 0).toFixed(2) }}</template>
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
        description="当前筛选条件下没有历史订单记录。"
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

.panel-alert {
  margin-bottom: 16px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
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
