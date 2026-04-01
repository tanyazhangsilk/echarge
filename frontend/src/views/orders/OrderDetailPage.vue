<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ROLES, getStoredOperatorId } from '../../config/permissions'
import { useOrderStore } from '../../stores/order'

const route = useRoute()
const router = useRouter()
const orderStore = useOrderStore()

const currentRole = computed(() => (route.meta?.role === ROLES.ADMIN ? ROLES.ADMIN : ROLES.OPERATOR))
const scope = computed(() => ({
  role: currentRole.value,
  operatorId: getStoredOperatorId(),
}))

const orderId = computed(() => String(route.params.id || ''))
const order = computed(() => orderStore.getOrderById(orderId.value, scope.value) || null)

const backPath = computed(() => {
  if (currentRole.value === ROLES.ADMIN) {
    return '/admin/orders'
  }
  return '/operator/orders/history'
})

const statusTagType = (status?: string): 'success' | 'warning' | 'danger' => {
  if (status === 'charging') return 'warning'
  if (status === 'abnormal') return 'danger'
  return 'success'
}

const statusText = (status?: string): string => {
  if (status === 'charging') return '充电中'
  if (status === 'abnormal') return '异常'
  return '已完成'
}

const payStatusText = (status?: string): string => {
  if (status === 'paid') return '已支付'
  if (status === 'refunded') return '已退款'
  return '待支付'
}

const formatMoney = (value: number): string =>
  `¥${Number(value || 0).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`

const goBack = () => {
  router.push(backPath.value)
}
</script>

<template>
  <div class="page-shell">
    <el-card v-if="order" shadow="never" class="surface-card">
      <template #header>
        <div class="header-row">
          <div>
            <h3>订单详情</h3>
            <p>{{ order.orderNo }}</p>
          </div>
          <el-button @click="goBack">返回列表</el-button>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="订单编号">{{ order.orderNo }}</el-descriptions-item>
        <el-descriptions-item label="订单状态">
          <el-tag :type="statusTagType(order.status)">{{ statusText(order.status) }}</el-tag>
        </el-descriptions-item>

        <el-descriptions-item label="用户">{{ order.userName }}</el-descriptions-item>
        <el-descriptions-item label="手机号">{{ order.phone }}</el-descriptions-item>
        <el-descriptions-item label="VIN">{{ order.vin }}</el-descriptions-item>
        <el-descriptions-item label="运营商">{{ order.operatorName }}</el-descriptions-item>

        <el-descriptions-item label="电站">{{ order.stationName }}</el-descriptions-item>
        <el-descriptions-item label="电桩">{{ order.chargerName }}</el-descriptions-item>
        <el-descriptions-item label="开始时间">{{ order.startTime }}</el-descriptions-item>
        <el-descriptions-item label="结束时间">{{ order.endTime || '-' }}</el-descriptions-item>

        <el-descriptions-item label="充电时长">{{ order.chargeDuration }} 分钟</el-descriptions-item>
        <el-descriptions-item label="充电电量">{{ Number(order.chargeAmount).toFixed(2) }} kWh</el-descriptions-item>
        <el-descriptions-item label="电费">{{ formatMoney(order.electricityFee) }}</el-descriptions-item>
        <el-descriptions-item label="服务费">{{ formatMoney(order.serviceFee) }}</el-descriptions-item>
        <el-descriptions-item label="总金额">{{ formatMoney(order.totalAmount) }}</el-descriptions-item>
        <el-descriptions-item label="支付状态">{{ payStatusText(order.payStatus) }}</el-descriptions-item>

        <el-descriptions-item v-if="order.status === 'abnormal'" label="异常原因" :span="2">
          {{ order.abnormalReason || '-' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-empty v-else description="未找到订单或无权查看该订单">
      <el-button type="primary" @click="goBack">返回订单列表</el-button>
    </el-empty>
  </div>
</template>

<style scoped>
.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.header-row h3 {
  margin: 0;
  font-size: 18px;
}

.header-row p {
  margin: 6px 0 0;
  color: var(--color-text-3);
}
</style>
