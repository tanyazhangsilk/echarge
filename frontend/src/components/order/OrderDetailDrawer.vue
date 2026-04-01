<script setup lang="ts">
import { computed } from 'vue'
import type { Order } from '../../types/order'

const props = defineProps<{
  visible: boolean
  order: Order | null
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
}>()

const drawerVisible = computed({
  get: () => props.visible,
  set: (value: boolean) => emit('update:visible', value),
})

const formatMoney = (value: number): string =>
  `¥${Number(value || 0).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`

const statusTagType = (status?: string): 'success' | 'warning' | 'danger' => {
  if (status === 'charging') return 'warning'
  if (status === 'abnormal') return 'danger'
  return 'success'
}

const statusText = (status?: string): string => {
  if (status === 'charging') return '充电中'
  if (status === 'abnormal') return '异常订单'
  return '已完成'
}

const payStatusText = (status?: string): string => {
  if (status === 'paid') return '已支付'
  if (status === 'refunded') return '已退款'
  return '待支付'
}
</script>

<template>
  <el-drawer v-model="drawerVisible" size="50%" direction="rtl">
    <template #header>
      <div class="drawer-title">订单详情 {{ order?.orderNo || '' }}</div>
    </template>

    <div v-if="order" class="drawer-body">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="订单编号">{{ order.orderNo }}</el-descriptions-item>
        <el-descriptions-item label="订单状态">
          <el-tag :type="statusTagType(order.status)">{{ statusText(order.status) }}</el-tag>
        </el-descriptions-item>

        <el-descriptions-item label="用户昵称">{{ order.userName }}</el-descriptions-item>
        <el-descriptions-item label="手机号">{{ order.phone }}</el-descriptions-item>
        <el-descriptions-item label="VIN">{{ order.vin }}</el-descriptions-item>
        <el-descriptions-item label="运营商名称">{{ order.operatorName }}</el-descriptions-item>

        <el-descriptions-item label="电站名称">{{ order.stationName }}</el-descriptions-item>
        <el-descriptions-item label="电桩名称">{{ order.chargerName }}</el-descriptions-item>
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

      <div class="drawer-footer">
        <el-button @click="drawerVisible = false">关闭</el-button>
      </div>
    </div>
  </el-drawer>
</template>

<style scoped>
.drawer-title {
  font-weight: 700;
  color: #409eff;
}

.drawer-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
}
</style>
