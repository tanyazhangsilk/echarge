<script setup>
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Lightning, Money, Tickets, Wallet } from '@element-plus/icons-vue'

import http from '../../api/http'

const dateRange = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)

const tableData = ref(
  [
    {
      id: 1005,
      settle_date: '2026-03-05',
      order_count: 150,
      total_amount: 13150.0,
      platform_fee: 1315.0,
      settle_amount: 11835.0,
      status: 0,
      created_at: '2026-03-06 00:01:12',
      updated_at: '2026-03-06 00:01:12',
    },
    {
      id: 1004,
      settle_date: '2026-03-04',
      order_count: 162,
      total_amount: 14200.0,
      platform_fee: 1420.0,
      settle_amount: 12780.0,
      status: 0,
      created_at: '2026-03-05 00:01:08',
      updated_at: '2026-03-05 00:01:08',
    },
    {
      id: 1003,
      settle_date: '2026-03-03',
      order_count: 138,
      total_amount: 11850.0,
      platform_fee: 1185.0,
      settle_amount: 10665.0,
      status: 1,
      created_at: '2026-03-04 00:00:56',
      updated_at: '2026-03-04 09:30:10',
    },
    {
      id: 1002,
      settle_date: '2026-03-02',
      order_count: 156,
      total_amount: 13620.5,
      platform_fee: 1362.05,
      settle_amount: 12258.45,
      status: 1,
      created_at: '2026-03-03 00:00:44',
      updated_at: '2026-03-03 10:15:22',
    },
    {
      id: 1001,
      settle_date: '2026-03-01',
      order_count: 145,
      total_amount: 12580.0,
      platform_fee: 1258.0,
      settle_amount: 11322.0,
      status: 1,
      created_at: '2026-03-02 00:00:31',
      updated_at: '2026-03-02 08:20:05',
    },
  ].sort((a, b) => b.settle_date.localeCompare(a.settle_date)),
)

const formatMoney = (amount) => {
  const num = Number(amount || 0)
  return num.toLocaleString('zh-CN', { minimumFractionDigits: 2 })
}

const summary = computed(() => {
  return tableData.value.reduce((acc, curr) => {
    acc.total_amount += Number(curr.total_amount || 0)
    acc.platform_fee += Number(curr.platform_fee || 0)
    acc.settle_amount += Number(curr.settle_amount || 0)
    return acc
  }, { total_amount: 0, platform_fee: 0, settle_amount: 0 })
})

const handleExport = () => {
  console.log('导出报表')
}

const getStatusType = (status) => {
  return status === 1 ? 'success' : 'warning'
}

const getStatusText = (status) => {
  return status === 1 ? '已打款' : '待打款'
}

const pagedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return tableData.value.slice(start, start + pageSize.value)
})

const handleManualSettle = () => {
  const now = new Date()
  const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000)
  const yyyy = yesterday.getFullYear()
  const mm = String(yesterday.getMonth() + 1).padStart(2, '0')
  const dd = String(yesterday.getDate()).padStart(2, '0')
  const dateStr = `${yyyy}-${mm}-${dd}`

  loading.value = true
  http
    .post('/settlements/manual_settle', { date: dateStr })
    .then((res) => {
      const processed = res?.data?.processed ?? 0
      ElMessage.success(`清分指令已下发，成功处理 ${processed}  笔订单`)
    })
    .catch(() => {
      ElMessage.error('清分指令下发失败，请稍后重试')
    })
    .finally(() => {
      setTimeout(() => {
        loading.value = false
      }, 300)
    })
}
</script>

<template>
  <div class="page-container">
    <el-row :gutter="20" class="stat-row">
      <el-col :xs="24" :sm="8">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-bar stat-bar--primary"></div>
          <div class="stat-head">
            <span class="stat-title">周期内订单总额</span>
            <el-icon class="stat-icon"><Wallet /></el-icon>
          </div>
          <div class="stat-value">￥ {{ formatMoney(summary.total_amount) }}</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-bar stat-bar--danger"></div>
          <div class="stat-head">
            <span class="stat-title">平台服务费(抽成)</span>
            <el-icon class="stat-icon"><Tickets /></el-icon>
          </div>
          <div class="stat-value">￥ {{ formatMoney(summary.platform_fee) }}</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-bar stat-bar--success"></div>
          <div class="stat-head">
            <span class="stat-title">预计可结算(实收)</span>
            <el-icon class="stat-icon"><Money /></el-icon>
          </div>
          <div class="stat-value">￥ {{ formatMoney(summary.settle_amount) }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="base-card">
      <el-row type="flex" justify="space-between" align="middle" class="action-bar">
        <el-date-picker
          v-model="dateRange"
          aria-label="选择结算日期范围"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 320px"
        />
        <div class="action-right">
          <el-button
            type="primary"
            color="#722ed1"
            :icon="Lightning"
            :loading="loading"
            aria-label="手动执行昨日清分"
            @click="handleManualSettle"
          >
            手动执行昨日清分
          </el-button>
          <el-button :icon="Download" aria-label="导出对账单" @click="handleExport">导出对账单</el-button>
        </div>
      </el-row>

      <el-table
        :data="pagedData"
        stripe
        :border="false"
        v-loading="loading"
        style="width: 100%"
        aria-label="清分结算明细表"
      >
        <el-table-column prop="settle_date" label="结算日期" min-width="140" />
        <el-table-column prop="order_count" label="订单笔数" width="100" />
        <el-table-column prop="total_amount" label="订单总额(元)" min-width="160" align="right">
          <template #default="{ row }">￥ {{ formatMoney(row.total_amount) }}</template>
        </el-table-column>
        <el-table-column prop="platform_fee" label="平台抽成(元)" min-width="160" align="right">
          <template #default="{ row }">￥ {{ formatMoney(row.platform_fee) }}</template>
        </el-table-column>
        <el-table-column prop="settle_amount" label="应结算金额(元)" min-width="160" align="right">
          <template #default="{ row }">
            <span class="amount-strong">￥ {{ formatMoney(row.settle_amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="打款状态" width="110">
          <template #default="{ row }">
            <el-tag v-if="row.status === 0" type="warning">待打款</el-tag>
            <el-tag v-else type="success">已打款</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column prop="updated_at" label="更新时间" width="180" />
      </el-table>

      <div class="pager">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="tableData.length"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.page-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stat-row {
  margin-bottom: 4px;
}

.stat-card {
  position: relative;
  overflow: hidden;
}

.stat-bar {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
}

.stat-bar--primary {
  background: #409eff;
}

.stat-bar--danger {
  background: #f56c6c;
}

.stat-bar--success {
  background: #67c23a;
}

.stat-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-left: 8px;
}

.stat-title {
  font-size: 14px;
  color: var(--text-regular);
}

.stat-icon {
  font-size: 36px;
  opacity: 0.15;
}

.stat-value {
  margin-left: 8px;
  margin-top: 10px;
  font-size: 28px;
  font-weight: 800;
  color: var(--text-primary);
}

.action-bar {
  margin-bottom: 12px;
}

.action-right {
  display: flex;
  gap: 12px;
}

.amount-strong {
  font-weight: 700;
  color: #67c23a;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 14px;
}
</style>
