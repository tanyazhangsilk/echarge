<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import EmptyStateBlock from '../../components/console/EmptyStateBlock.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import { fetchOperatorDashboard } from '../../api/console'

const loading = ref(false)
const cards = ref([])
const profile = ref(null)
const stationHealth = ref([])
const orderTrend = ref([])
const alarms = ref([])
const realtimeOrders = ref([])

const maxOrderCount = computed(() => Math.max(1, ...orderTrend.value.map((item) => item.orderCount)))

const loadData = async () => {
  loading.value = true
  try {
    const { data } = await fetchOperatorDashboard()
    profile.value = data.profile
    cards.value = data.cards
    stationHealth.value = data.stationHealth
    orderTrend.value = data.orderTrend
    alarms.value = data.alarms
    realtimeOrders.value = data.realtimeOrders
  } catch (error) {
    console.error(error)
    ElMessage.error('运营商工作台加载失败。')
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div class="page-shell">
    <PageSectionHeader
      eyebrow="Operator Console"
      title="运营中心工作台"
      description="面向充电运营商的日常运营首页，聚焦订单、营收、电站健康、设备告警和实时充电订单，适合作为论文截图中的运营侧主页面。"
      chip="运营商视角"
    >
      <template #actions>
        <el-button>导出日报</el-button>
        <el-button type="primary">发起巡检</el-button>
      </template>
    </PageSectionHeader>

    <section v-if="profile" class="operator-banner surface-card">
      <div>
        <h3>{{ profile.operatorName }}</h3>
        <p>{{ profile.region }} · {{ profile.stationCount }} 座电站 · {{ profile.connectorCount }} 个枪口</p>
      </div>
      <div class="operator-banner__meta">
        <span>设备在线率</span>
        <strong>{{ profile.onlineRate }}%</strong>
      </div>
    </section>

    <section class="stats-grid">
      <MetricCard
        v-for="item in cards"
        :key="item.label"
        :label="item.label"
        :value="item.value"
        :prefix="item.prefix"
        :suffix="item.unit || item.suffix"
        :trend="item.trend"
        :tone="item.tone"
      />
    </section>

    <section class="split-layout">
      <article class="page-panel surface-card">
        <div class="panel-heading">
          <div>
            <h3 class="panel-heading__title">近 7 日订单趋势</h3>
            <p class="panel-heading__desc">为后续接订单统计接口预留趋势展示区，目前以真实业务字段命名的 mock 数据填充。</p>
          </div>
        </div>

        <div class="order-trend">
          <div v-for="item in orderTrend" :key="item.date" class="order-trend__row">
            <span class="order-trend__date">{{ item.date }}</span>
            <div class="order-trend__track">
              <div class="order-trend__fill" :style="{ width: `${(item.orderCount / maxOrderCount) * 100}%` }"></div>
            </div>
            <strong>{{ item.orderCount }}</strong>
            <span class="order-trend__revenue">¥{{ item.revenue.toLocaleString() }}</span>
          </div>
        </div>
      </article>

      <article class="page-panel surface-card">
        <div class="panel-heading">
          <div>
            <h3 class="panel-heading__title">电站健康概况</h3>
            <p class="panel-heading__desc">适合作为运营视角的右侧摘要区。</p>
          </div>
        </div>
        <div class="info-list">
          <div v-for="item in stationHealth" :key="item.status" class="list-card health-card">
            <strong class="list-card__title">{{ item.status }}</strong>
            <p class="list-card__meta">{{ item.count }} 座电站</p>
          </div>
        </div>
      </article>
    </section>

    <section class="panel-grid">
      <article class="page-panel surface-card">
        <div class="panel-heading">
          <div>
            <h3 class="panel-heading__title">设备告警</h3>
            <p class="panel-heading__desc">保留设备告警列表，为后续接入告警中心或工单系统预留入口。</p>
          </div>
        </div>
        <div class="alarm-list">
          <div v-for="item in alarms" :key="item.id" class="list-card">
            <div class="alarm-head">
              <strong class="list-card__title">{{ item.stationName }}</strong>
              <el-tag :type="item.level === 'high' ? 'danger' : item.level === 'medium' ? 'warning' : 'info'">
                {{ item.level === 'high' ? '高告警' : item.level === 'medium' ? '中告警' : '低告警' }}
              </el-tag>
            </div>
            <p class="list-card__meta">{{ item.equipmentCode }} · {{ item.issue }}</p>
            <p class="list-card__meta">{{ item.detectedAt }} · {{ item.suggestion }}</p>
          </div>
        </div>
      </article>

      <article class="page-panel surface-card table-shell">
        <div class="panel-heading">
          <div>
            <h3 class="panel-heading__title">实时充电订单</h3>
            <p class="panel-heading__desc">用于展示进行中订单，后续可直接接实时订单接口或 websocket。</p>
          </div>
        </div>
        <el-table v-loading="loading" :data="realtimeOrders" size="small">
          <el-table-column prop="orderNo" label="订单号" min-width="180" />
          <el-table-column prop="vehiclePlate" label="车牌号" width="100" />
          <el-table-column prop="stationName" label="电站" min-width="180" />
          <el-table-column prop="connectorName" label="设备" min-width="150" />
          <el-table-column prop="chargedKwh" label="电量(kWh)" width="110" />
          <el-table-column label="金额" width="100">
            <template #default="{ row }">¥{{ row.amount }}</template>
          </el-table-column>
          <el-table-column label="状态" width="120">
            <template #default="{ row }">
              <el-tag :type="row.status === 'charging' ? 'success' : 'warning'">
                {{ row.status === 'charging' ? '充电中' : '待结算' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>

        <EmptyStateBlock
          v-if="!loading && realtimeOrders.length === 0"
          title="当前暂无实时订单"
          description="后续接入实时订单接口后，可在此展示正在充电或待结算的订单。"
        />
      </article>
    </section>
  </div>
</template>

<style scoped>
.operator-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 24px;
}

.operator-banner h3 {
  margin: 0;
  font-size: 22px;
}

.operator-banner p {
  margin: 8px 0 0;
  color: var(--color-text-2);
}

.operator-banner__meta {
  text-align: right;
}

.operator-banner__meta span {
  display: block;
  color: var(--color-text-3);
  font-size: 12px;
}

.operator-banner__meta strong {
  font-size: 28px;
  color: var(--color-primary-strong);
}

.order-trend {
  display: grid;
  gap: 12px;
}

.order-trend__row {
  display: grid;
  grid-template-columns: 56px minmax(0, 1fr) 60px 110px;
  gap: 12px;
  align-items: center;
}

.order-trend__date,
.order-trend__revenue {
  color: var(--color-text-3);
  font-size: 13px;
}

.order-trend__track {
  height: 12px;
  border-radius: 999px;
  background: var(--color-surface-3);
  overflow: hidden;
}

.order-trend__fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #2f74ff, #6aa7ff);
}

.health-card {
  text-align: center;
}

.alarm-list {
  display: grid;
  gap: 12px;
}

.alarm-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

@media (max-width: 768px) {
  .operator-banner {
    flex-direction: column;
    align-items: flex-start;
  }

  .operator-banner__meta {
    text-align: left;
  }

  .order-trend__row {
    grid-template-columns: 1fr;
  }
}
</style>
