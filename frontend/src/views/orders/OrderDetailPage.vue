<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Clock, Document, Money, WarningFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import EmptyStateBlock from '../../components/console/EmptyStateBlock.vue'
import { fetchAdminOrderDetail } from '../../api/admin'
import { fetchOperatorOrderDetail } from '../../api/operator'
import { ROLES } from '../../config/permissions'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const order = ref(null)

const formatMoney = (value) => `¥${Number(value || 0).toFixed(2)}`
const isAdmin = computed(() => route.meta?.role === ROLES.ADMIN)

const summaryCards = computed(() => {
  if (!order.value) return []
  return [
    {
      label: '订单状态',
      value: order.value.status_text,
      trend: '生命周期节点',
      trendLabel: '充电中 / 已完成 / 异常结束',
      tone: order.value.status === 2 ? 'danger' : order.value.status === 1 ? 'success' : 'warning',
      icon: Document,
    },
    {
      label: '充电时长',
      value: order.value.charge_duration,
      suffix: ' 分钟',
      trend: '本次会话时长',
      trendLabel: '适合展示充电过程',
      tone: 'primary',
      icon: Clock,
    },
    {
      label: '总费用',
      value: Number(order.value.total_amount || 0).toFixed(2),
      prefix: '¥',
      trend: '电费 + 服务费',
      trendLabel: '结算字段自动生成',
      tone: 'warning',
      icon: Money,
    },
    {
      label: '异常标记',
      value: order.value.abnormal_reason ? '已记录' : '无',
      trend: order.value.abnormal_reason || '当前无异常说明',
      trendLabel: '异常订单会显示具体原因',
      tone: order.value.abnormal_reason ? 'danger' : 'info',
      icon: WarningFilled,
    },
  ]
})

const timelineItems = computed(() => {
  if (!order.value) return []
  const items = [
    {
      type: 'primary',
      title: '开始充电',
      time: order.value.start_time,
      content: `电站：${order.value.station_name}，电桩：${order.value.charger_name}`,
    },
  ]

  if (order.value.end_time) {
    items.push({
      type: order.value.status === 2 ? 'danger' : 'success',
      title: order.value.status === 2 ? '异常结束' : '完成订单',
      time: order.value.end_time,
      content: order.value.status === 2 ? order.value.abnormal_reason || '运营商手动标记异常' : '订单已转入历史订单',
    })
  } else {
    items.push({
      type: 'warning',
      title: '充电进行中',
      time: order.value.updated_at,
      content: '当前订单仍处于实时充电状态，可结束充电或标记异常。',
    })
  }

  return items
})

const loadOrder = async () => {
  loading.value = true
  try {
    const response = isAdmin.value
      ? await fetchAdminOrderDetail(route.params.id)
      : await fetchOperatorOrderDetail(route.params.id)
    order.value = response.data.data || null
  } catch (error) {
    console.error(error)
    ElMessage.error('订单详情加载失败')
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.push(isAdmin.value ? '/admin/orders' : '/operator/orders/history')
}

onMounted(loadOrder)
</script>

<template>
  <div class="page-shell detail-page">
    <PageSectionHeader
      eyebrow="Order Detail"
      title="订单详情"
      description="通过卡片、金额区块、描述列表和时间线展示完整订单信息，适合单独截图。"
      :chip="isAdmin ? '管理员订单管理' : '运营商订单管理'"
    >
      <template #actions>
        <el-button @click="goBack">返回列表</el-button>
      </template>
    </PageSectionHeader>

    <template v-if="order">
      <section class="stats-grid stats-grid--detail">
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

      <section class="detail-grid">
        <article class="page-panel surface-card">
          <div class="panel-heading">
            <div>
              <h3 class="panel-heading__title">订单信息</h3>
              <p class="panel-heading__desc">{{ order.order_no }}</p>
            </div>
          </div>

          <div class="amount-banner">
            <div class="amount-banner__item">
              <span>电费</span>
              <strong>{{ formatMoney(order.electricity_fee) }}</strong>
            </div>
            <div class="amount-banner__item">
              <span>服务费</span>
              <strong>{{ formatMoney(order.service_fee) }}</strong>
            </div>
            <div class="amount-banner__item amount-banner__item--highlight">
              <span>总费用</span>
              <strong>{{ formatMoney(order.total_amount) }}</strong>
            </div>
          </div>

          <el-descriptions :column="2" border class="detail-descriptions">
            <el-descriptions-item label="订单编号">{{ order.order_no }}</el-descriptions-item>
            <el-descriptions-item label="订单状态">
              <el-tag :type="order.status === 2 ? 'danger' : order.status === 1 ? 'success' : 'warning'">
                {{ order.status_text }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="用户账号">{{ order.user_phone }}</el-descriptions-item>
            <el-descriptions-item label="用户昵称">{{ order.user_nickname }}</el-descriptions-item>
            <el-descriptions-item label="VIN">{{ order.vin || '-' }}</el-descriptions-item>
            <el-descriptions-item label="运营商名称">{{ order.operator_name }}</el-descriptions-item>
            <el-descriptions-item label="开始时间">{{ order.start_time }}</el-descriptions-item>
            <el-descriptions-item label="结束时间">{{ order.end_time || '-' }}</el-descriptions-item>
            <el-descriptions-item label="充电时长">{{ order.charge_duration }} 分钟</el-descriptions-item>
            <el-descriptions-item label="充电电量">{{ Number(order.charge_amount).toFixed(2) }} kWh</el-descriptions-item>
            <el-descriptions-item label="支付状态">{{ order.pay_status_text }}</el-descriptions-item>
            <el-descriptions-item label="电站名称">{{ order.station_name }}</el-descriptions-item>
            <el-descriptions-item label="电桩名称">{{ order.charger_name }}</el-descriptions-item>
            <el-descriptions-item label="异常原因" :span="2">
              {{ order.abnormal_reason || '无异常原因' }}
            </el-descriptions-item>
          </el-descriptions>
        </article>

        <article class="page-panel surface-card">
          <div class="panel-heading">
            <div>
              <h3 class="panel-heading__title">状态流转</h3>
              <p class="panel-heading__desc">按时间线展示订单从开始充电到结束的关键节点。</p>
            </div>
          </div>

          <el-timeline>
            <el-timeline-item
              v-for="item in timelineItems"
              :key="`${item.title}-${item.time}`"
              :type="item.type"
              :timestamp="item.time"
              placement="top"
            >
              <div class="timeline-card">
                <strong>{{ item.title }}</strong>
                <p>{{ item.content }}</p>
              </div>
            </el-timeline-item>
          </el-timeline>
        </article>
      </section>
    </template>

    <section v-else class="page-panel surface-card">
      <EmptyStateBlock title="未找到订单" description="当前订单不存在，或没有权限查看该订单。" />
    </section>
  </div>
</template>

<style scoped>
.detail-page {
  padding-bottom: 8px;
}

.stats-grid--detail {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.detail-grid {
  display: grid;
  grid-template-columns: 1.35fr 0.85fr;
  gap: 20px;
}

.amount-banner {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}

.amount-banner__item {
  display: grid;
  gap: 8px;
  padding: 16px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(47, 116, 255, 0.08), rgba(73, 187, 174, 0.1));
}

.amount-banner__item--highlight {
  background: linear-gradient(135deg, rgba(255, 176, 32, 0.16), rgba(255, 115, 0, 0.16));
}

.amount-banner__item span {
  color: var(--color-text-2);
  font-size: 13px;
}

.amount-banner__item strong {
  font-size: 26px;
  color: var(--color-text);
}

.detail-descriptions :deep(.el-descriptions__label) {
  width: 120px;
}

.timeline-card {
  padding: 14px 16px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(47, 116, 255, 0.06), rgba(73, 187, 174, 0.08));
}

.timeline-card strong {
  display: block;
  margin-bottom: 8px;
}

.timeline-card p {
  margin: 0;
  color: var(--color-text-2);
  line-height: 1.6;
}

@media (max-width: 1280px) {
  .stats-grid--detail {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .stats-grid--detail,
  .amount-banner {
    grid-template-columns: 1fr;
  }
}
</style>
