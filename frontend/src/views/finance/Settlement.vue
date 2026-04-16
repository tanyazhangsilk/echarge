<script setup>
import { computed, onMounted, ref } from 'vue'
import {
  Document,
  Download,
  Money,
  Reading,
  RefreshRight,
  Tickets,
  Wallet,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import EmptyStateBlock from '../../components/console/EmptyStateBlock.vue'
import http from '../../api/http'

const loading = ref(false)
const rows = ref([])
const dateRange = ref([])
const currentPage = ref(1)
const pageSize = ref(20)

const explainVisible = ref(false)
const detailVisible = ref(false)
const detailLoading = ref(false)
const activeBatch = ref(null)
const detailOrders = ref([])

const formatMoney = (value) => {
  const num = Number(value || 0)
  return num.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const normalizeRow = (row) => ({
  id: row.id ?? null,
  settle_date: row.settle_date,
  operator_id: row.operator_id ?? null,
  operator_name: row.operator_name || '当前运营商',
  order_count: Number(row.order_count || 0),
  total_amount: Number(row.total_amount || 0),
  platform_fee: Number(row.platform_fee || 0),
  settle_amount: Number(row.settle_amount || 0),
  platform_rate: row.platform_rate == null ? null : Number(row.platform_rate),
  status: Number(row.status ?? 0),
  status_text: row.status_text || '',
  can_payout: row.can_payout,
  hold_reason: row.hold_reason || '',
  created_at: row.created_at || '',
  updated_at: row.updated_at || '',
})

const inDateRange = (dateText) => {
  if (!Array.isArray(dateRange.value) || dateRange.value.length !== 2) return true
  if (!dateText) return false
  const [startText, endText] = dateRange.value
  const current = new Date(`${dateText}T00:00:00`)
  const start = new Date(`${startText}T00:00:00`)
  const end = new Date(`${endText}T23:59:59`)
  return current >= start && current <= end
}

const filteredRows = computed(() => rows.value.filter((row) => inDateRange(row.settle_date)))

const pagedRows = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredRows.value.slice(start, start + pageSize.value)
})

const summary = computed(() => {
  const totalAmount = filteredRows.value.reduce((sum, row) => sum + row.total_amount, 0)
  const platformFee = filteredRows.value.reduce((sum, row) => sum + row.platform_fee, 0)
  const settleAmount = filteredRows.value.reduce((sum, row) => sum + row.settle_amount, 0)
  const paidAmount = filteredRows.value
    .filter((row) => row.status === 1)
    .reduce((sum, row) => sum + row.settle_amount, 0)
  const pendingAmount = filteredRows.value
    .filter((row) => row.status !== 1)
    .reduce((sum, row) => sum + row.settle_amount, 0)

  return {
    totalAmount,
    platformFee,
    settleAmount,
    paidAmount,
    pendingAmount,
  }
})

const statCards = computed(() => [
  {
    label: '周期内订单总额',
    value: formatMoney(summary.value.totalAmount),
    prefix: '¥',
    trend: '经营流水总览',
    trendLabel: '按清分周期聚合',
    tone: 'primary',
    icon: Wallet,
  },
  {
    label: '平台服务费',
    value: formatMoney(summary.value.platformFee),
    prefix: '¥',
    trend: '平台抽成部分',
    trendLabel: '随订单规模波动',
    tone: 'warning',
    icon: Tickets,
  },
  {
    label: '应结算金额',
    value: formatMoney(summary.value.settleAmount),
    prefix: '¥',
    trend: '本周期理论应收',
    trendLabel: '扣除平台费后',
    tone: 'success',
    icon: Money,
  },
  {
    label: '已打款金额',
    value: formatMoney(summary.value.paidAmount),
    prefix: '¥',
    trend: '到账已确认',
    trendLabel: '状态为已打款',
    tone: 'info',
    icon: Document,
  },
  {
    label: '待打款金额',
    value: formatMoney(summary.value.pendingAmount),
    prefix: '¥',
    trend: '需跟进批次',
    trendLabel: '含待补资料场景',
    tone: 'danger',
    icon: Reading,
  },
])

const payoutStatusType = (status) => {
  if (status === 1) return 'success'
  if (status === 2) return 'danger'
  return 'warning'
}

const payoutStatusText = (row) => {
  if (row.status_text) return row.status_text
  if (row.status === 1) return '已打款'
  if (row.status === 2) return '挂起待补资料'
  return '待打款'
}

const qualificationType = (row) => {
  if (row.can_payout === true) return 'success'
  if (row.can_payout === false) return 'warning'
  return 'info'
}

const qualificationText = (row) => {
  if (row.can_payout === true) return '资格通过'
  if (row.can_payout === false) return '待补资料'
  return '未判定'
}

const payoutRate = computed(() => {
  const total = summary.value.settleAmount
  if (!total) return 0
  return Math.round((summary.value.paidAmount / total) * 100)
})

const fetchRows = async (silent = false) => {
  if (!silent) loading.value = true
  try {
    const resp = await http.get('/finance/settlements')
    const payload = resp?.data || {}
    const list = Array.isArray(payload.data) ? payload.data : []
    rows.value = list.map(normalizeRow).sort((a, b) => String(b.settle_date).localeCompare(String(a.settle_date)))
  } catch (error) {
    ElMessage.error('加载对账数据失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const refreshData = async () => {
  await fetchRows()
  ElMessage.success('对账数据已刷新')
}

const exportStatement = () => {
  if (!filteredRows.value.length) {
    ElMessage.warning('当前筛选范围无可导出数据')
    return
  }
  const headers = [
    '清分日期',
    '订单数',
    '订单总额(元)',
    '平台服务费(元)',
    '应结算金额(元)',
    '资格状态',
    '打款状态',
    '备注',
  ]
  const lines = [headers.join(',')]
  for (const row of filteredRows.value) {
    const cells = [
      row.settle_date,
      row.order_count,
      row.total_amount.toFixed(2),
      row.platform_fee.toFixed(2),
      row.settle_amount.toFixed(2),
      qualificationText(row),
      payoutStatusText(row),
      row.hold_reason || '',
    ]
    lines.push(cells.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(','))
  }

  const csvContent = `\uFEFF${lines.join('\n')}`
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  const suffix = new Date().toISOString().slice(0, 10)
  link.href = url
  link.download = `运营商收益对账单_${suffix}.csv`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  ElMessage.success('对账单导出成功')
}

const openBatchDetail = async (row) => {
  activeBatch.value = row
  detailVisible.value = true
  detailLoading.value = true
  detailOrders.value = []
  try {
    const resp = await http.get('/operator/orders/history', {
      params: {
        page: 1,
        page_size: 200,
      },
    })
    const list = resp?.data?.data?.items || []
    const orders = list
      .filter(
        (item) =>
          String(item.end_time || '').startsWith(row.settle_date) &&
          Number(item.order_status_code) === 1 &&
          Number(item.pay_status) === 1 &&
          Number(item.settlement_status) === 1,
      )
      .map((item) => ({
        order_no: item.order_no,
        user_phone: item.user_phone || '-',
        station_name: item.station_name || '-',
        start_time: item.start_time || '-',
        end_time: item.end_time || '-',
        charge_amount: Number(item.charge_amount || 0),
        total_amount: Number(item.total_amount || 0),
      }))
    detailOrders.value = orders
  } catch (error) {
    ElMessage.error('加载批次订单明细失败')
  } finally {
    detailLoading.value = false
  }
}

onMounted(() => {
  fetchRows()
})
</script>

<template>
  <div class="page-shell settlement-page">
    <PageSectionHeader
      eyebrow="Revenue Reconciliation"
      title="运营商收益对账"
      description="仅展示当前运营商清分记录，用于核对服务费、应结算金额与打款状态。"
      chip="运营商财务管理"
    >
      <template #actions>
        <el-button :icon="RefreshRight" @click="refreshData">刷新对账数据</el-button>
        <el-button type="info" plain @click="explainVisible = true">查看结算说明</el-button>
      </template>
    </PageSectionHeader>

    <section class="stats-grid stats-grid--settlement">
      <MetricCard
        v-for="item in statCards"
        :key="item.label"
        :label="item.label"
        :value="item.value"
        :prefix="item.prefix"
        :trend="item.trend"
        :trend-label="item.trendLabel"
        :tone="item.tone"
        :icon="item.icon"
      />
    </section>

    <section class="panel-grid panel-grid--wide">
      <article class="page-panel surface-card">
        <div class="panel-heading">
          <div>
            <h3 class="panel-heading__title">打款进度</h3>
            <p class="panel-heading__desc">展示当前筛选范围内结算金额的到账比例。</p>
          </div>
        </div>

        <div class="payout-progress">
          <div class="payout-progress__head">
            <strong>已打款占比</strong>
            <span>{{ payoutRate }}%</span>
          </div>
          <el-progress :percentage="payoutRate" :stroke-width="12" :show-text="false" color="#22a06b" />
          <div class="payout-progress__meta">
            <span>已打款 ¥{{ formatMoney(summary.paidAmount) }}</span>
            <span>待打款 ¥{{ formatMoney(summary.pendingAmount) }}</span>
          </div>
        </div>
      </article>

      <article class="page-panel surface-card">
        <div class="panel-heading">
          <div>
            <h3 class="panel-heading__title">筛选与导出</h3>
            <p class="panel-heading__desc">按日期范围筛选并导出对账单，支持财务留档。</p>
          </div>
        </div>

        <div class="filter-box">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            value-format="YYYY-MM-DD"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            range-separator="至"
            style="width: 320px"
          />
          <el-button type="primary" :icon="Download" @click="exportStatement">导出对账单</el-button>
        </div>
      </article>
    </section>

    <section class="page-panel surface-card table-shell" v-loading="loading">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">清分记录</h3>
          <p class="panel-heading__desc">列表仅展示当前运营商自己的批次记录。</p>
        </div>
      </div>

      <el-table v-if="pagedRows.length" :data="pagedRows" stripe border>
        <el-table-column prop="settle_date" label="清分日期" min-width="120" />
        <el-table-column prop="order_count" label="订单数" width="90" align="center" />
        <el-table-column prop="total_amount" label="订单总额(元)" min-width="130" align="right">
          <template #default="{ row }">¥{{ formatMoney(row.total_amount) }}</template>
        </el-table-column>
        <el-table-column prop="platform_fee" label="平台服务费(元)" min-width="130" align="right">
          <template #default="{ row }">¥{{ formatMoney(row.platform_fee) }}</template>
        </el-table-column>
        <el-table-column prop="settle_amount" label="应结算金额(元)" min-width="130" align="right">
          <template #default="{ row }">
            <span class="amount-strong">¥{{ formatMoney(row.settle_amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="运营商资格状态" width="130" align="center">
          <template #default="{ row }">
            <el-tag :type="qualificationType(row)" effect="dark" size="small">
              {{ qualificationText(row) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="打款状态" width="130" align="center">
          <template #default="{ row }">
            <el-tag :type="payoutStatusType(row.status)" size="small">
              {{ payoutStatusText(row) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="备注" min-width="160">
          <template #default="{ row }">
            <span v-if="row.hold_reason" class="text-warning">{{ row.hold_reason }}</span>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right" align="center">
          <template #default="{ row }">
            <el-button link type="primary" @click="openBatchDetail(row)">查看明细</el-button>
          </template>
        </el-table-column>
      </el-table>

      <EmptyStateBlock v-else-if="!loading" title="暂无清分记录" description="当前筛选范围暂无数据，可调整日期范围后重试。" />

      <div class="pager">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="filteredRows.length"
        />
      </div>
    </section>

    <el-drawer
      v-model="detailVisible"
      size="56%"
      :title="`清分订单明细 · ${activeBatch?.settle_date || '-'}`"
      destroy-on-close
    >
      <el-alert
        type="info"
        :closable="false"
        class="mb-4"
        title="按清分归属日展示已完成且已结算订单，用于运营商与平台财务对账。"
      />

      <el-descriptions :column="3" border class="mb-4" v-if="activeBatch">
        <el-descriptions-item label="清分日期">{{ activeBatch.settle_date }}</el-descriptions-item>
        <el-descriptions-item label="订单数">{{ activeBatch.order_count }}</el-descriptions-item>
        <el-descriptions-item label="应结算金额">¥{{ formatMoney(activeBatch.settle_amount) }}</el-descriptions-item>
      </el-descriptions>

      <el-table :data="detailOrders" stripe border v-loading="detailLoading">
        <el-table-column prop="order_no" label="订单号" min-width="190" />
        <el-table-column prop="user_phone" label="用户手机号" width="120" />
        <el-table-column prop="station_name" label="充电站" min-width="140" />
        <el-table-column prop="start_time" label="开始时间" width="160" />
        <el-table-column prop="end_time" label="结束时间" width="160" />
        <el-table-column prop="charge_amount" label="充电量(kWh)" width="120" align="right">
          <template #default="{ row }">{{ Number(row.charge_amount).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="total_amount" label="订单金额(元)" width="120" align="right">
          <template #default="{ row }">¥{{ formatMoney(row.total_amount) }}</template>
        </el-table-column>
      </el-table>
    </el-drawer>

    <el-dialog v-model="explainVisible" title="结算说明" width="560px">
      <div class="explain">
        <p>1. 平台采用 T+1 清分：按订单结束时间的自然日归属。</p>
        <p>2. 运营商清分资格要求：已认证 + 默认有效银行卡。</p>
        <p>3. 资料不全时批次会标记为“挂起待补资料”，不会中断其他运营商清分。</p>
        <p>4. 对账差异建议核查：订单支付状态、异常订单、银行卡绑定状态。</p>
      </div>
      <template #footer>
        <el-button type="primary" @click="explainVisible = false">我知道了</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.settlement-page {
  padding-bottom: 10px;
}

.stats-grid--settlement {
  grid-template-columns: repeat(5, minmax(0, 1fr));
}

.payout-progress {
  padding: 14px;
  border: 1px solid var(--color-border);
  border-radius: 14px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.88), rgba(247, 251, 255, 0.92));
}

.payout-progress__head {
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.payout-progress__head strong {
  color: var(--color-text);
}

.payout-progress__head span {
  color: #22a06b;
  font-weight: 700;
}

.payout-progress__meta {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  color: var(--color-text-2);
  font-size: 12px;
}

.filter-box {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.amount-strong {
  color: #16a34a;
  font-weight: 700;
}

.text-warning {
  color: #e6a23c;
}

.text-muted {
  color: #909399;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 14px;
}

.mb-4 {
  margin-bottom: 16px;
}

.explain {
  line-height: 1.9;
  color: #4b5563;
}

@media (max-width: 1440px) {
  .stats-grid--settlement {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .stats-grid--settlement {
    grid-template-columns: 1fr;
  }
}
</style>
