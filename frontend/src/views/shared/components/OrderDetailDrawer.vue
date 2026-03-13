<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  order: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['update:modelValue'])

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})
</script>

<template>
  <el-drawer v-model="visible" title="订单详情" size="40%">
    <el-descriptions :column="1" border>
      <el-descriptions-item label="订单号">{{ order.orderNo || '-' }}</el-descriptions-item>
      <el-descriptions-item label="充电量(kWh)">{{ order.energy || '-' }}</el-descriptions-item>
      <el-descriptions-item label="充电时长(min)">{{ order.duration || '-' }}</el-descriptions-item>
      <el-descriptions-item label="订单金额(元)">{{ order.amount || '-' }}</el-descriptions-item>
      <el-descriptions-item label="订单状态">{{ order.status || '-' }}</el-descriptions-item>
    </el-descriptions>

    <template #footer>
      <!-- 业务页面调用此组件时，通过 actions 插槽注入当前角色专属的操作按钮（如管理员注入驳回，运营商注入退款） -->
      <slot name="actions" />
    </template>
  </el-drawer>
</template>
