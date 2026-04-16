<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Bell, Money, RefreshRight, WarningFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import EmptyStateBlock from '../../components/console/EmptyStateBlock.vue'
import { fetchAdminAbnormalOrders } from '../../api/admin'
import { fetchOperatorAbnormalOrders } from '../../api/operator'
import { ROLES } from '../../config/permissions'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const errorMessage = ref('')
const orders = ref([])
const total = ref(0)

const pagination = reactive({
  page: 1,
  pageSize: 10,
})

const filters = reactive({
  keyword: '',
  reason: '',
  dateRange: [],
})

const summary = reactive({
  total_count: 0,
  total_amount: 0,
  reason_count: 0,
  abnormal_count: 0,
})

let searchTimer = null

const isAdmin = computed(() => route.meta?.role === ROLES.ADMIN)
const formatMoney = (value) => `¥${Number(value || 0).toFixed(2)}`

const stats = computed(() => [
  {
    label: '异常订单',
    value: summary.total_count,
    suffix: ' 单',
    trend: '当前筛选条件下的异常订单',
    trendLabel: '支持按原因与时间范围查询',
    tone: 'danger',
    icon: WarningFilled,
  },
  {
    label: '异常金额',
    value: Number(summary.total_amount || 0).toFixed(2),
    prefix: '¥',
    trend: '异常订单涉及金额',
    trendLabel: '用于财务核查',
    tone: 'warning',
    icon: Money,
  },
  {
    label: '异常类型',
    value: summary.reason_count,
    suffix: ' 类',
    trend: '异常原因种类数',
    trendLabel: '按异常原因归类统计',
    tone: 'info',
    icon: Bell,
  },
  {
    label: '待处理数量',
    value: summary.abnormal_count,
    suffix: ' 单',
    trend: '异常状态订单数量',
    trendLabel: '用于安排处理优先级',
    tone: 'primary',
    icon: RefreshRight,
  },
])

const buildQueryParams = () => ({
  page: pagination.page,
  page_size: pagination.pageSize,
  keyword: filters.keyword.trim() || undefined,
  abnormal_reason: filters.reason.trim() || undefined,
  start_date: filters.dateRange?.[0] || undefined,
  end_date: filters.dateRange?.[1] || undefined,
})

const loadOrders = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const response = isAdmin.value
      ? await fetchAdminAbnormalOrders(buildQueryParams())
      : await fetchOperatorAbnormalOrders(buildQueryParams())

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
      total_amount: 0,
      reason_count: 0,
      abnormal_count: 0,
    })
    errorMessage.value = error?.response?.data?.message || error?.response?.data?.detail || '异常订单加载失败，请稍后重试。'
    ElMessage.error(errorMessage.value)
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.keyword = ''
  filters.reason = ''
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
  () => [filters.keyword, filters.reason, JSON.stringify(filters.dateRange)],
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

onMounted(loadOrders)

onBeforeUnmount(() => {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
})
</script>

<template>
  <div class="page-shell abnormal-page">
    <PageSectionHeader
      eyebrow="订单中心"
      :title="isAdmin ? '异常订单管理' : '异常订单'"
      description="查询异常订单及异常原因，跟踪处理情况。"
      :chip="isAdmin ? '平台订单' : '订单中心'"
    >
      <template #actions>
        <el-button :icon="RefreshRight" :loading="loading" @click="loadOrders">刷新列表</el-button>
      </template>
    </PageSectionHeader>

    <section class="stats-grid stats-grid--abnormal">
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
          <p class="panel-heading__desc">支持按订单、用户、异常原因和时间范围查询。</p>
        </div>
        <div class="toolbar-actions">
          <el-button @click="resetFilters">重置</el-button>
        </div>
      </div>

      <div class="filter-row">
        <el-input v-model="filters.keyword" clearable placeholder="订单号 / 用户账号 / VIN / 电站" style="width: 320px" />
        <el-input v-model="filters.reason" clearable placeholder="输入异常原因关键词" style="width: 240px" />
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
        <el-table-column label="用户" min-width="160">
          <template #default="{ row }">
            <div class="user-cell">
              <strong>{{ row.user_nickname }}</strong>
              <span>{{ row.user_phone }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="vin" label="VIN" min-width="170" show-overflow-tooltip />
        <el-table-column prop="start_time" label="开始时间" width="170" />
        <el-table-column prop="end_time" label="结束时间" width="170" />
        <el-table-column prop="station_name" label="电站" min-width="170" show-overflow-tooltip />
        <el-table-column prop="charger_name" label="电桩" min-width="160" show-overflow-tooltip />
        <el-table-column label="异常原因" min-width="260">
          <template #default="{ row }">
            <div class="reason-pill">{{ row.abnormal_reason || '未记录异常原因' }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="total_amount" label="总费用" width="110" align="right">
          <template #default="{ row }">{{ formatMoney(row.total_amount) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="danger">{{ row.status_text }}</el-tag>
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
        title="暂无异常订单"
        description="当前筛选条件下没有异常订单记录。"
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
.abnormal-page {
  padding-bottom: 8px;
}

.stats-grid--abnormal {
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

.user-cell {
  display: grid;
  gap: 4px;
}

.user-cell span {
  color: var(--color-text-2);
}

.reason-pill {
  padding: 10px 12px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(245, 108, 108, 0.18), rgba(255, 182, 93, 0.22));
  color: #b42318;
  font-weight: 600;
  line-height: 1.5;
}

@media (max-width: 1280px) {
  .stats-grid--abnormal {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .stats-grid--abnormal {
    grid-template-columns: 1fr;
  }
}
</style>
