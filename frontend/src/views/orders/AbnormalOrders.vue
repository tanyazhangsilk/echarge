<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
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
const orders = ref([])

const filters = reactive({
  keyword: '',
  reason: '',
})

const formatMoney = (value) => `¥${Number(value || 0).toFixed(2)}`
const isAdmin = computed(() => route.meta?.role === ROLES.ADMIN)

const filteredOrders = computed(() => {
  const keyword = filters.keyword.trim().toLowerCase()
  const reasonKeyword = filters.reason.trim().toLowerCase()
  return orders.value.filter((item) => {
    const matchKeyword =
      !keyword ||
      [item.order_no, item.user_phone, item.user_nickname, item.vin, item.station_name]
        .filter(Boolean)
        .some((field) => String(field).toLowerCase().includes(keyword))
    const matchReason =
      !reasonKeyword || String(item.abnormal_reason || '').toLowerCase().includes(reasonKeyword)
    return matchKeyword && matchReason
  })
})

const stats = computed(() => {
  const totalCount = filteredOrders.value.length
  const totalAmount = filteredOrders.value.reduce((sum, item) => sum + Number(item.total_amount || 0), 0)
  const reasonCount = new Set(filteredOrders.value.map((item) => item.abnormal_reason).filter(Boolean)).size
  const highRiskCount = filteredOrders.value.filter((item) =>
    ['断连', '故障', '支付', '异常'].some((keyword) => String(item.abnormal_reason || '').includes(keyword)),
  ).length

  return [
    {
      label: '异常订单',
      value: totalCount,
      suffix: ' 单',
      trend: '待复核订单',
      trendLabel: '用于风控和答辩展示',
      tone: 'danger',
      icon: WarningFilled,
    },
    {
      label: '异常金额',
      value: totalAmount.toFixed(2),
      prefix: '¥',
      trend: '异常订单涉及金额',
      trendLabel: '便于展示财务影响',
      tone: 'warning',
      icon: Money,
    },
    {
      label: '异常类型',
      value: reasonCount,
      suffix: ' 类',
      trend: '异常原因种类',
      trendLabel: '可做论文图表说明',
      tone: 'info',
      icon: Bell,
    },
    {
      label: '高风险异常',
      value: highRiskCount,
      suffix: ' 单',
      trend: '支付/设备相关',
      trendLabel: '建议重点展示原因',
      tone: 'primary',
      icon: RefreshRight,
    },
  ]
})

const loadOrders = async () => {
  loading.value = true
  try {
    const response = isAdmin.value ? await fetchAdminAbnormalOrders() : await fetchOperatorAbnormalOrders()
    orders.value = response.data.data || []
  } catch (error) {
    console.error(error)
    ElMessage.error('异常订单加载失败')
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.keyword = ''
  filters.reason = ''
}

const openDetail = (row) => {
  router.push(isAdmin.value ? `/admin/orders/detail/${row.id}` : `/operator/orders/detail/${row.id}`)
}

onMounted(loadOrders)
</script>

<template>
  <div class="page-shell abnormal-page">
    <PageSectionHeader
      eyebrow="Abnormal Orders"
      :title="isAdmin ? '全局异常订单' : '异常订单'"
      :description="isAdmin ? '管理员查看全平台异常订单。' : '突出展示异常原因与异常金额，便于论文截图和答辩时说明订单异常处理闭环。'"
      :chip="isAdmin ? '管理员订单管理' : '运营商订单管理'"
    >
      <template #actions>
        <el-button :icon="RefreshRight" :loading="loading" @click="loadOrders">刷新列表</el-button>
      </template>
    </PageSectionHeader>

    <el-alert
      title="异常原因在列表中采用高亮色块展示，便于截图时一眼看出问题点。"
      type="warning"
      show-icon
      :closable="false"
      class="risk-alert"
    />

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
          <p class="panel-heading__desc">支持按订单号、用户、VIN 和异常原因关键词筛选。</p>
        </div>
        <div class="toolbar-actions">
          <el-button @click="resetFilters">重置</el-button>
        </div>
      </div>

      <div class="filter-row">
        <el-input v-model="filters.keyword" clearable placeholder="订单号 / 用户账号 / VIN / 电站" style="width: 320px" />
        <el-input v-model="filters.reason" clearable placeholder="输入异常原因关键词" style="width: 240px" />
      </div>
    </section>

    <section class="page-panel surface-card table-shell">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">异常订单列表</h3>
          <p class="panel-heading__desc">共 {{ filteredOrders.length }} 条记录，支持跳转订单详情页查看完整信息。</p>
        </div>
      </div>

      <el-table v-if="filteredOrders.length" :data="filteredOrders" v-loading="loading" stripe>
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
        description="当前没有异常订单，可以先在实时订单页把一条订单标记为异常。"
      />
    </section>
  </div>
</template>

<style scoped>
.abnormal-page {
  padding-bottom: 8px;
}

.risk-alert {
  margin-bottom: 18px;
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
