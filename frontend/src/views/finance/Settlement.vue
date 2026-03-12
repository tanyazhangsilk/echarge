<script setup>
import { onMounted, onUnmounted, reactive, ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Lightning, Money, Tickets, Wallet } from '@element-plus/icons-vue'
import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg =
      err?.response?.data?.message ||
      err?.response?.data?.detail ||
      err?.response?.data?.msg ||
      err?.message ||
      '请求失败'
    err._uiMessage = msg
    return Promise.reject(err)
  }
)

const dateRange = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const tableData = ref([])
const summary = reactive({ total_amount: 0, platform_fee: 0, settle_amount: 0 })

let abortController

const formatMoney = (amount) => {
  const num = Number(amount || 0)
  return num.toLocaleString('zh-CN', { minimumFractionDigits: 2 })
}

const resetSummary = () => {
  summary.total_amount = 0
  summary.platform_fee = 0
  summary.settle_amount = 0
}

const loadData = async () => {
  try {
    loading.value = true
    abortController?.abort()
    abortController = new AbortController()
    const res = await api.get('/finance/settlements', { signal: abortController.signal })
    const rows = Array.isArray(res?.data?.data) ? res.data.data : []
    tableData.value = rows
      .map((r) => ({
        ...r,
        total_amount: Number(r.total_amount || 0),
        platform_fee: Number(r.platform_fee || 0),
        settle_amount: Number(r.settle_amount || 0),
      }))
      .sort((a, b) => String(b.settle_date).localeCompare(String(a.settle_date)))
    resetSummary()
    for (const r of tableData.value) {
      summary.total_amount += Number(r.total_amount || 0) || 0
      summary.platform_fee += Number(r.platform_fee || 0) || 0
      summary.settle_amount += Number(r.settle_amount || 0) || 0
    }
    loading.value = false
  } catch (e) {
    loading.value = false
    const msg = e?._uiMessage || e?.message || '请求失败'
    ElMessage.error(`获取结算列表失败：${msg}`)
    tableData.value = []
    resetSummary()
  }
}

const handleExport = () => {
  ElMessage.success('已开始导出对账单')
}

const getStatusType = (status) => (status === 1 ? 'success' : 'warning')
const getStatusText = (status) => (status === 1 ? '已打款' : '待打款')

const pagedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return tableData.value.slice(start, start + pageSize.value)
})

const handleManualSettle = async () => {
  try {
    loading.value = true
    const res = await api.post('/finance/settle')
    const msg = res?.data?.message || '清分请求已完成'
    ElMessage.success(msg)
    await loadData()
    loading.value = false
  } catch (e) {
    loading.value = false
    const msg = e?._uiMessage || e?.message || '清分请求失败'
    ElMessage.error(`清分请求失败：${msg}`)
  }
}

onMounted(() => {
  loadData()
})

onUnmounted(() => {
  abortController?.abort()
})
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

    <el-card shadow="never" class="base-card" v-loading="loading">
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
