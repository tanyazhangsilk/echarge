<script setup>
import { ref, computed } from 'vue'
import { Download } from '@element-plus/icons-vue'

const dateRange = ref([])

// Mock 收益明细数据 (5条)
const tableData = ref([
  {
    date: '2026-03-01',
    orderCount: 145,
    totalAmount: 12580.00,
    platformFee: 1258.00,
    settleAmount: 11322.00,
    status: 'settled'
  },
  {
    date: '2026-03-02',
    orderCount: 156,
    totalAmount: 13620.50,
    platformFee: 1362.05,
    settleAmount: 12258.45,
    status: 'settled'
  },
  {
    date: '2026-03-03',
    orderCount: 138,
    totalAmount: 11850.00,
    platformFee: 1185.00,
    settleAmount: 10665.00,
    status: 'settled'
  },
  {
    date: '2026-03-04',
    orderCount: 162,
    totalAmount: 14200.00,
    platformFee: 1420.00,
    settleAmount: 12780.00,
    status: 'pending'
  },
  {
    date: '2026-03-05',
    orderCount: 150,
    totalAmount: 13150.00,
    platformFee: 1315.00,
    settleAmount: 11835.00,
    status: 'pending'
  }
])

// 计算属性：统计总额、抽成、实收
const summary = computed(() => {
  return tableData.value.reduce((acc, curr) => {
    acc.totalAmount += curr.totalAmount
    acc.platformFee += curr.platformFee
    acc.settleAmount += curr.settleAmount
    return acc
  }, { totalAmount: 0, platformFee: 0, settleAmount: 0 })
})

const handleExport = () => {
  console.log('导出报表')
}

const getStatusType = (status) => {
  return status === 'settled' ? 'success' : 'warning'
}

const getStatusText = (status) => {
  return status === 'settled' ? '已清分' : '待清分'
}
</script>

<template>
  <div class="page-container flex flex-col gap-4">
    <!-- 顶部统计卡片 -->
    <el-row :gutter="16">
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover" class="mb-4 sm:mb-0 text-center">
          <div class="text-gray-500 text-sm mb-2">周期内订单总额</div>
          <div class="text-2xl font-bold text-gray-800">¥ {{ summary.totalAmount.toFixed(2) }}</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover" class="mb-4 sm:mb-0 text-center">
          <div class="text-gray-500 text-sm mb-2">平台服务费(抽成)</div>
          <div class="text-2xl font-bold text-red-500">- ¥ {{ summary.platformFee.toFixed(2) }}</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover" class="text-center">
          <div class="text-gray-500 text-sm mb-2">预计可结算(实收)</div>
          <div class="text-2xl font-bold text-green-500">¥ {{ summary.settleAmount.toFixed(2) }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 列表区域 -->
    <el-card shadow="never" class="base-card flex-1">
      <div class="flex justify-between items-center mb-4">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 300px"
        />
        <el-button type="primary" plain :icon="Download" @click="handleExport">导出对账单</el-button>
      </div>

      <el-table :data="tableData" style="width: 100%" v-loading="false">
        <el-table-column prop="date" label="结算日期" min-width="120" />
        <el-table-column prop="orderCount" label="订单笔数" width="100" />
        <el-table-column prop="totalAmount" label="订单总额(元)" min-width="120">
          <template #default="{ row }">¥ {{ row.totalAmount.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="platformFee" label="平台抽成(元)" min-width="120">
          <template #default="{ row }">- ¥ {{ row.platformFee.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="settleAmount" label="结算金额(元)" min-width="120">
          <template #default="{ row }">
            <span class="font-bold text-green-600">¥ {{ row.settleAmount.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="打款状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default>
            <el-button link type="primary" size="small">明细</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
/* 样式已使用 Tailwind 类名替代 */
</style>
