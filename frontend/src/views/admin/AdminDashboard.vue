<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import {
  Coin,
  Connection,
  DocumentChecked,
  Lightning,
  Money,
  OfficeBuilding,
  Tickets,
  WarningFilled,
} from '@element-plus/icons-vue'

import EmptyStateBlock from '../../components/console/EmptyStateBlock.vue'
import DonutStatusChart from '../../components/console/DonutStatusChart.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import TrendAreaChart from '../../components/console/TrendAreaChart.vue'
import { fetchAdminDashboard } from '../../api/console'
import { ROLES } from '../../config/permissions'
import { useOrderStore } from '../../stores/order'

const router = useRouter()
const orderStore = useOrderStore()

const loading = ref(false)
const baseOverviewStats = ref([])
const baseDistributions = ref(null)
const todoList = ref([])
const recentActivities = ref([])
const announcements = ref([])
const adminScope = { role: ROLES.ADMIN }

const orderStats = computed(() => orderStore.getOrderStats(adminScope))
const orderTrendSource = computed(() => orderStore.getOrderTrend(adminScope, 7))
const allOrders = computed(() => orderStore.getAllOrders(adminScope))

const overviewStats = computed(() =>
  baseOverviewStats.value.map((item) => {
    if (item.key === 'todayOrderCount') {
      return { ...item, value: allOrders.value.length }
    }
    if (item.key === 'todayRevenue') {
      return { ...item, value: orderStats.value.todayTotalAmount.toFixed(2) }
    }
    if (item.key === 'abnormalOrderCount') {
      return { ...item, value: orderStats.value.abnormalCount }
    }
    return item
  }),
)

const orderTrend = computed(() =>
  orderTrendSource.value.map((item) => ({
    date: item.date,
    orderCount: item.orderCount,
  })),
)

const revenueTrend = computed(() =>
  orderTrendSource.value.map((item) => ({
    date: item.date,
    revenue: item.revenue,
  })),
)

const distributions = computed(() => {
  const source = baseDistributions.value || {}
  const chargingCount = allOrders.value.filter((item) => item.status === 'charging').length
  const completedCount = allOrders.value.filter((item) => item.status === 'completed').length
  const abnormalCount = allOrders.value.filter((item) => item.status === 'abnormal').length
  return {
    ...source,
    orderStatus: {
      total: allOrders.value.length,
      totalLabel: '订单总数',
      items: [
        { label: '充电中', value: chargingCount, color: '#2f74ff' },
        { label: '已完成', value: completedCount, color: '#22a06b' },
        { label: '异常', value: abnormalCount, color: '#d84f57' },
      ],
    },
  }
})

const abnormalOrders = computed(() =>
  orderStore.getAbnormalOrders(adminScope).slice(0, 6).map((order) => ({
    id: order.id,
    orderNo: order.orderNo,
    userName: order.userName,
    stationName: order.stationName,
    abnormalType: order.abnormalReason || '异常',
    createdAt: (order.updatedAt || order.startTime || '').replace('T', ' ').slice(0, 16),
    status: '待复核',
  })),
)

const iconMap = {
  OfficeBuilding,
  DocumentChecked,
  Lightning,
  Connection,
  Tickets,
  Money,
  Coin,
  WarningFilled,
}

const currentDateText = computed(() => dayjs().format('YYYY年MM月DD日 dddd'))

const summaryText = computed(() => {
  const statsMap = Object.fromEntries(overviewStats.value.map((item) => [item.key, item]))
  const operatorTotal = statsMap.operatorTotal?.value ?? '--'
  const stationTotal = statsMap.stationTotal?.value ?? '--'
  const todayOrderCount = statsMap.todayOrderCount?.value ?? '--'
  return `当前平台已接入 ${operatorTotal} 家运营商、${stationTotal} 座电站，今日累计订单 ${todayOrderCount} 单。`
})

const decoratedOverviewStats = computed(() =>
  overviewStats.value.map((item) => ({
    ...item,
    label: item.title,
    icon: iconMap[item.icon] || null,
  })),
)

const abnormalTagType = (status) => {
  if (status === '处理中') return 'warning'
  if (status === '待复核') return 'danger'
  return 'info'
}

const announcementTagType = (level) => {
  if (level === 'warning') return 'warning'
  if (level === 'success') return 'success'
  return 'info'
}

const loadData = async () => {
  loading.value = true
  try {
    const { data } = await fetchAdminDashboard()
    baseOverviewStats.value = data.overviewStats || []
    baseDistributions.value = data.distributions || null
    todoList.value = data.todoList || []
    recentActivities.value = data.recentActivities || []
    announcements.value = data.announcements || []
  } catch (error) {
    console.error(error)
    ElMessage.error('平台工作台加载失败，请检查 mock 数据或接口配置。')
  } finally {
    loading.value = false
  }
}

const goToTodo = (item) => {
  if (item.route) router.push(item.route)
}

const goToOrderDetail = (row) => {
  router.push(`/admin/orders/detail/${row.id}`)
}

onMounted(loadData)
</script>

<template>
  <div class="page-shell admin-dashboard">
    <PageSectionHeader
      eyebrow="Admin Console"
      title="平台工作台"
      description="展示平台运营、审核和订单概况"
      chip="平台管理员视角"
    >
      <template #actions>
        <div class="hero-meta">
          <span class="hero-meta__date">{{ currentDateText }}</span>
          <el-button @click="loadData">刷新数据</el-button>
          <el-button type="primary" @click="router.push('/admin/institutions')">运营商审核</el-button>
        </div>
      </template>
    </PageSectionHeader>

    <section class="hero-banner surface-card">
      <div class="hero-banner__content">
        <p class="hero-banner__label">平台概览</p>
        <h2 class="hero-banner__title">面向平台运营、审核与风控的一体化首页</h2>
        <p class="hero-banner__desc">{{ summaryText }}</p>
      </div>
      <div class="hero-banner__actions">
        <el-button plain @click="router.push('/admin/institutions/stations')">电站审核</el-button>
        <el-button plain @click="router.push('/admin/finance')">进入清分中心</el-button>
        <el-button type="primary" plain @click="router.push('/admin/orders/abnormal')">异常订单监管</el-button>
      </div>
    </section>

    <section class="stats-grid stats-grid--dashboard">
      <MetricCard
        v-for="item in decoratedOverviewStats"
        :key="item.key"
        :label="item.label"
        :value="item.value"
        :prefix="item.prefix"
        :suffix="item.suffix"
        :trend="item.trend"
        :trend-label="item.trendLabel"
        :trend-direction="item.trendDirection"
        :tone="item.tone"
        :icon="item.icon"
      />
    </section>

    <section class="panel-grid">
      <TrendAreaChart
        title="近 7 日订单趋势图"
        subtitle="展示平台近 7 日订单规模变化，可直接替换为订单统计接口。"
        :data="orderTrend"
        y-field="orderCount"
        :loading="loading"
      />
      <TrendAreaChart
        title="近 7 日交易额趋势图"
        subtitle="按自然日展示平台交易额走势，便于观察日度交易波动。"
        :data="revenueTrend"
        y-field="revenue"
        color="#22a06b"
        area-color="rgba(34, 160, 107, 0.16)"
        :value-formatter="(value) => `¥${Number(value).toLocaleString()}`"
        :loading="loading"
      />
    </section>

    <section class="panel-grid distribution-grid">
      <DonutStatusChart
        title="运营商审核状态分布"
        subtitle="反映平台当前运营商接入审核整体情况。"
        :items="distributions?.operatorAudit?.items || []"
        :total="distributions?.operatorAudit?.total"
        :total-label="distributions?.operatorAudit?.totalLabel"
        :loading="loading"
      />
      <DonutStatusChart
        title="电站状态分布"
        subtitle="聚焦已运营、维护中和待审核电站结构。"
        :items="distributions?.stationStatus?.items || []"
        :total="distributions?.stationStatus?.total"
        :total-label="distributions?.stationStatus?.totalLabel"
        :loading="loading"
      />
      <DonutStatusChart
        title="订单状态分布"
        subtitle="从运营视角查看今日订单完成与异常占比。"
        :items="distributions?.orderStatus?.items || []"
        :total="distributions?.orderStatus?.total"
        :total-label="distributions?.orderStatus?.totalLabel"
        :loading="loading"
      />
    </section>

    <section class="panel-grid panel-grid--wide">
      <article class="page-panel surface-card" v-loading="loading">
        <div class="panel-heading">
          <div>
            <h3 class="panel-heading__title">待处理事项</h3>
            <p class="panel-heading__desc">集中展示平台当前需要优先跟进的审核、财务和异常事务。</p>
          </div>
        </div>

        <div v-if="todoList.length" class="todo-list">
          <button
            v-for="item in todoList"
            :key="item.id"
            type="button"
            class="todo-item"
            @click="goToTodo(item)"
          >
            <div class="todo-item__main">
              <div class="todo-item__title-row">
                <strong>{{ item.title }}</strong>
                <el-tag size="small" effect="plain">{{ item.priority }}</el-tag>
              </div>
              <p class="todo-item__desc">{{ item.description }}</p>
            </div>
            <div class="todo-item__side">
              <span class="todo-item__count">{{ item.count }}</span>
              <span class="todo-item__action">{{ item.actionText }}</span>
            </div>
          </button>
        </div>

        <EmptyStateBlock
          v-else-if="!loading"
          title="当前暂无待处理事项"
          description="待办数据为空时，将在这里展示默认空状态。"
        />
      </article>

      <article class="page-panel surface-card table-shell" v-loading="loading">
        <div class="panel-heading">
          <div>
            <h3 class="panel-heading__title">最近异常订单</h3>
            <p class="panel-heading__desc">用于展示最新进入异常流程的订单，并支持跳转到异常订单监管页面。</p>
          </div>
        </div>

        <el-table v-if="abnormalOrders.length" :data="abnormalOrders">
          <el-table-column prop="orderNo" label="订单编号" min-width="180" />
          <el-table-column prop="userName" label="用户" width="110" />
          <el-table-column prop="stationName" label="电站" min-width="180" />
          <el-table-column prop="abnormalType" label="异常类型" min-width="150" />
          <el-table-column prop="createdAt" label="创建时间" width="150" />
          <el-table-column label="状态" width="110">
            <template #default="{ row }">
              <el-tag :type="abnormalTagType(row.status)">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="110" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link @click="goToOrderDetail(row)">查看详情</el-button>
            </template>
          </el-table-column>
        </el-table>

        <EmptyStateBlock
          v-else-if="!loading"
          title="暂无异常订单"
          description="当平台没有进入异常流程的订单时，这里会展示空状态。"
        />
      </article>
    </section>

    <section class="panel-grid">
      <article class="page-panel surface-card" v-loading="loading">
        <div class="panel-heading">
          <div>
            <h3 class="panel-heading__title">最近动态</h3>
            <p class="panel-heading__desc">记录平台最新发生的审核、风控和配置调整事件。</p>
          </div>
        </div>

        <div v-if="recentActivities.length" class="activity-list">
          <div v-for="item in recentActivities" :key="item.id" class="activity-item">
            <div class="activity-item__dot"></div>
            <div class="activity-item__content">
              <div class="activity-item__head">
                <strong>{{ item.title }}</strong>
                <span>{{ item.time }}</span>
              </div>
              <p>{{ item.description }}</p>
            </div>
          </div>
        </div>

        <EmptyStateBlock
          v-else-if="!loading"
          title="暂无最近动态"
          description="后续接入动态流接口后，可在此处展示更完整的平台事件。"
        />
      </article>

      <article class="page-panel surface-card" v-loading="loading">
        <div class="panel-heading">
          <div>
            <h3 class="panel-heading__title">平台公告</h3>
            <p class="panel-heading__desc">适合论文截图展示，也为后续公告接口预留清晰结构。</p>
          </div>
        </div>

        <div v-if="announcements.length" class="info-list">
          <div v-for="item in announcements" :key="item.id" class="info-item notice-card">
            <div class="notice-card__head">
              <strong class="info-item__title">{{ item.title }}</strong>
              <el-tag :type="announcementTagType(item.level)">
                {{ item.level === 'warning' ? '提示' : item.level === 'success' ? '已生效' : '公告' }}
              </el-tag>
            </div>
            <p class="info-item__desc">{{ item.content }}</p>
          </div>
        </div>

        <EmptyStateBlock
          v-else-if="!loading"
          title="暂无平台公告"
          description="公告数据为空时，这里会保留空状态占位。"
        />
      </article>
    </section>
  </div>
</template>

<style scoped>
.admin-dashboard {
  padding-bottom: 8px;
}

.hero-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
}

.hero-meta__date {
  color: var(--color-text-3);
  font-size: 13px;
}

.hero-banner {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding: 26px 28px;
  background:
    radial-gradient(circle at right top, rgba(47, 116, 255, 0.16), transparent 34%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(246, 249, 252, 0.94));
}

.hero-banner__content {
  max-width: 760px;
}

.hero-banner__label {
  margin: 0;
  color: var(--color-primary-strong);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.hero-banner__title {
  margin: 10px 0 0;
  font-size: 28px;
  line-height: 1.2;
  color: var(--color-text);
}

.hero-banner__desc {
  margin: 12px 0 0;
  color: var(--color-text-2);
  line-height: 1.7;
}

.hero-banner__actions {
  display: grid;
  gap: 12px;
  min-width: 220px;
}

.stats-grid--dashboard {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.distribution-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.todo-list,
.activity-list {
  display: grid;
  gap: 12px;
}

.todo-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  width: 100%;
  padding: 18px;
  border: 1px solid var(--color-border);
  border-radius: 16px;
  background: var(--color-surface-3);
  text-align: left;
  cursor: pointer;
  transition: transform var(--motion-fast) ease, border-color var(--motion-fast) ease, box-shadow var(--motion-fast) ease;
}

.todo-item:hover {
  transform: translateY(-2px);
  border-color: rgba(47, 116, 255, 0.22);
  box-shadow: 0 14px 28px rgba(15, 23, 42, 0.08);
}

.todo-item__main {
  min-width: 0;
}

.todo-item__title-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.todo-item__desc {
  margin: 10px 0 0;
  color: var(--color-text-2);
  line-height: 1.6;
}

.todo-item__side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  min-width: 72px;
}

.todo-item__count {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text);
}

.todo-item__action {
  color: var(--color-primary-strong);
  font-size: 13px;
}

.activity-item {
  display: grid;
  grid-template-columns: 16px minmax(0, 1fr);
  gap: 12px;
}

.activity-item__dot {
  position: relative;
  margin-top: 6px;
  width: 12px;
  height: 12px;
  border-radius: 999px;
  background: linear-gradient(135deg, #2f74ff, #22a06b);
  box-shadow: 0 0 0 4px rgba(47, 116, 255, 0.1);
}

.activity-item__content {
  padding-bottom: 14px;
  border-bottom: 1px dashed var(--color-border);
}

.activity-item__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.activity-item__head span {
  color: var(--color-text-3);
  font-size: 12px;
}

.activity-item__content p {
  margin: 8px 0 0;
  color: var(--color-text-2);
  line-height: 1.6;
}

.notice-card {
  background: linear-gradient(180deg, var(--color-surface-3), rgba(255, 255, 255, 0.85));
}

.notice-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

:root[data-theme='dark'] .hero-banner {
  background:
    radial-gradient(circle at right top, rgba(47, 116, 255, 0.22), transparent 34%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
}

@media (max-width: 1200px) {
  .distribution-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .hero-meta,
  .hero-banner,
  .todo-item,
  .activity-item__head {
    flex-direction: column;
    align-items: flex-start;
  }

  .hero-banner {
    padding: 20px;
  }

  .hero-banner__actions,
  .stats-grid--dashboard {
    grid-template-columns: 1fr;
  }

  .todo-item__side {
    align-items: flex-start;
  }
}
</style>
