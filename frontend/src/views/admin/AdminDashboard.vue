<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import EmptyStateBlock from '../../components/console/EmptyStateBlock.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import { fetchAdminDashboard } from '../../api/console'

const router = useRouter()

const loading = ref(false)
const keyword = ref('')
const riskFilter = ref('')
const queue = ref([])
const cards = ref([])
const trend = ref([])
const announcements = ref([])

const riskTagMap = {
  high: 'danger',
  medium: 'warning',
  low: 'success',
}

const filteredQueue = computed(() =>
  queue.value.filter((item) => {
    const matchKeyword =
      !keyword.value ||
      [item.id, item.applicantName, item.regionScope, item.contactName]
        .filter(Boolean)
        .some((field) => String(field).toLowerCase().includes(keyword.value.trim().toLowerCase()))
    const matchRisk = !riskFilter.value || item.riskLevel === riskFilter.value
    return matchKeyword && matchRisk
  }),
)

const maxTrendValue = computed(() =>
  Math.max(
    1,
    ...trend.value.map((item) => Math.max(item.operatorApprovals, item.stationApprovals, item.abnormalOrders)),
  ),
)

const loadData = async () => {
  loading.value = true
  try {
    const { data } = await fetchAdminDashboard()
    cards.value = data.cards
    trend.value = data.trend
    queue.value = data.auditQueue
    announcements.value = data.announcements
  } catch (error) {
    console.error(error)
    ElMessage.error('管理员工作台加载失败，当前请检查 mock 数据或接口配置。')
  } finally {
    loading.value = false
  }
}

const goToRecord = (item) => {
  if (item.applicantType === '省级运营商') {
    router.push('/admin/institutions')
    return
  }

  if (item.applicantType === '电站上架') {
    router.push('/admin/institutions/stations')
    return
  }

  router.push('/admin/orders/anomalies')
}

onMounted(loadData)
</script>

<template>
  <div class="page-shell">
    <PageSectionHeader
      eyebrow="Admin Console"
      title="平台治理工作台"
      description="面向平台管理员的聚合监管首页，聚焦准入审核、订单风控、清分监管和系统配置入口，适合作为论文截图首页与后续联调总入口。"
      chip="平台监管视角"
    >
      <template #actions>
        <el-button @click="router.push('/admin/institutions')">进入运营商审核</el-button>
        <el-button type="primary" @click="router.push('/admin/institutions/stations')">进入电站审核</el-button>
      </template>
    </PageSectionHeader>

    <section class="stats-grid">
      <MetricCard
        v-for="item in cards"
        :key="item.key"
        :label="item.label"
        :value="item.value"
        :prefix="item.prefix"
        :suffix="item.unit"
        :trend="item.trend"
        :tone="item.tone"
      />
    </section>

    <section class="split-layout">
      <article class="page-panel surface-card">
        <div class="panel-heading">
          <div>
            <h3 class="panel-heading__title">近 7 日平台审核与预警走势</h3>
            <p class="panel-heading__desc">用统一监管视角展示运营商审核、电站审核和异常订单数量变化，方便后续接真实统计接口。</p>
          </div>
        </div>

        <div class="trend-board">
          <div v-for="item in trend" :key="item.date" class="trend-row">
            <div class="trend-row__date">{{ item.date }}</div>
            <div class="trend-row__bars">
              <div class="trend-bar trend-bar--primary">
                <span class="trend-bar__label">运营商审核</span>
                <div class="trend-bar__track">
                  <div class="trend-bar__fill" :style="{ width: `${(item.operatorApprovals / maxTrendValue) * 100}%` }"></div>
                </div>
                <strong>{{ item.operatorApprovals }}</strong>
              </div>
              <div class="trend-bar trend-bar--warning">
                <span class="trend-bar__label">电站审核</span>
                <div class="trend-bar__track">
                  <div class="trend-bar__fill" :style="{ width: `${(item.stationApprovals / maxTrendValue) * 100}%` }"></div>
                </div>
                <strong>{{ item.stationApprovals }}</strong>
              </div>
              <div class="trend-bar trend-bar--danger">
                <span class="trend-bar__label">异常订单</span>
                <div class="trend-bar__track">
                  <div class="trend-bar__fill" :style="{ width: `${(item.abnormalOrders / maxTrendValue) * 100}%` }"></div>
                </div>
                <strong>{{ item.abnormalOrders }}</strong>
              </div>
            </div>
          </div>
        </div>
      </article>

      <div class="panel-stack">
        <article class="page-panel surface-card">
          <div class="panel-heading">
            <div>
              <h3 class="panel-heading__title">系统提示</h3>
              <p class="panel-heading__desc">保留适合论文展示的管理动作说明，同时也为后续公告接口预留结构。</p>
            </div>
          </div>
          <div class="info-list">
            <div v-for="item in announcements" :key="item.title" class="info-item">
              <div class="notice-head">
                <strong class="info-item__title">{{ item.title }}</strong>
                <el-tag :type="item.level === 'warning' ? 'warning' : item.level === 'success' ? 'success' : 'info'">
                  {{ item.level === 'warning' ? '提示' : item.level === 'success' ? '已就绪' : '说明' }}
                </el-tag>
              </div>
              <p class="info-item__desc">{{ item.content }}</p>
            </div>
          </div>
        </article>

        <article class="page-panel surface-card">
          <div class="panel-heading">
            <div>
              <h3 class="panel-heading__title">快捷入口</h3>
              <p class="panel-heading__desc">优先串起论文截图和主业务链路。</p>
            </div>
          </div>
          <div class="quick-actions">
            <el-button plain @click="router.push('/admin/institutions')">运营商审核</el-button>
            <el-button plain @click="router.push('/admin/institutions/stations')">电站审核</el-button>
            <el-button plain @click="router.push('/admin/orders')">全局订单</el-button>
            <el-button plain @click="router.push('/admin/finance')">清分结算</el-button>
          </div>
        </article>
      </div>
    </section>

    <article class="page-panel surface-card table-shell">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">平台待办队列</h3>
          <p class="panel-heading__desc">整合运营商审核、电站审核和订单预警，便于管理员从首页直接进入处理。</p>
        </div>
      </div>

      <div class="toolbar-row toolbar-row--wrap">
        <div class="toolbar-group">
          <el-input v-model="keyword" placeholder="搜索编号、主体名称、区域或责任人" clearable style="width: 320px;" />
          <el-select v-model="riskFilter" placeholder="风险等级" clearable style="width: 140px;">
            <el-option label="高风险" value="high" />
            <el-option label="中风险" value="medium" />
            <el-option label="低风险" value="low" />
          </el-select>
        </div>
        <div class="toolbar-group">
          <el-button @click="keyword = ''; riskFilter = ''">重置</el-button>
          <el-button type="primary" @click="loadData">刷新数据</el-button>
        </div>
      </div>

      <el-table v-loading="loading" :data="filteredQueue">
        <el-table-column prop="id" label="待办编号" min-width="160" />
        <el-table-column prop="applicantName" label="对象名称" min-width="200" />
        <el-table-column prop="applicantType" label="类型" width="120" />
        <el-table-column prop="regionScope" label="区域" min-width="160" />
        <el-table-column prop="licenseStatus" label="材料状态" min-width="160" />
        <el-table-column prop="submittedAt" label="提交时间" width="160" />
        <el-table-column label="风险等级" width="120">
          <template #default="{ row }">
            <el-tag :type="riskTagMap[row.riskLevel]">
              {{ row.riskLevel === 'high' ? '高风险' : row.riskLevel === 'medium' ? '中风险' : '低风险' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="goToRecord(row)">立即处理</el-button>
          </template>
        </el-table-column>
      </el-table>

      <EmptyStateBlock
        v-if="!loading && filteredQueue.length === 0"
        title="当前筛选条件下暂无待办"
        description="你可以清空筛选条件，或继续补充新的平台审核与风控数据。"
      />
    </article>
  </div>
</template>

<style scoped>
.trend-board {
  display: grid;
  gap: 14px;
}

.trend-row {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}

.trend-row__date {
  padding-top: 9px;
  color: var(--color-text-3);
  font-size: 13px;
}

.trend-row__bars {
  display: grid;
  gap: 10px;
}

.trend-bar {
  display: grid;
  grid-template-columns: 96px minmax(0, 1fr) 34px;
  gap: 12px;
  align-items: center;
}

.trend-bar__label {
  color: var(--color-text-2);
  font-size: 13px;
}

.trend-bar__track {
  height: 10px;
  border-radius: 999px;
  background: var(--color-surface-3);
  overflow: hidden;
}

.trend-bar__fill {
  height: 100%;
  border-radius: inherit;
}

.trend-bar--primary .trend-bar__fill {
  background: linear-gradient(90deg, #2f74ff, #77a7ff);
}

.trend-bar--warning .trend-bar__fill {
  background: linear-gradient(90deg, #e19a2b, #f4ca6a);
}

.trend-bar--danger .trend-bar__fill {
  background: linear-gradient(90deg, #db5a60, #f4a0a4);
}

.notice-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

@media (max-width: 768px) {
  .trend-row {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .trend-bar {
    grid-template-columns: 1fr;
  }

  .quick-actions {
    grid-template-columns: 1fr;
  }
}
</style>
