<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Search } from '@element-plus/icons-vue'
import { useOrderStore } from '../../stores/order'
import OrderDetailDrawer from '../../components/order/OrderDetailDrawer.vue'
import type { Order } from '../../types/order'

interface FilterForm {
  orderNo: string
  keyword: string
  stationName: string
  abnormalReason: string
}

const orderStore = useOrderStore()

const loading = ref(false)
const allOrders = ref<Order[]>([])
const currentPage = ref(1)
const pageSize = ref(10)
const drawerVisible = ref(false)
const currentOrderId = ref('')
const currentOrder = computed(() => orderStore.getOrderById(currentOrderId.value) || null)

const searchForm = reactive<FilterForm>({
  orderNo: '',
  keyword: '',
  stationName: '',
  abnormalReason: '',
})

const appliedFilters = reactive<FilterForm>({
  orderNo: '',
  keyword: '',
  stationName: '',
  abnormalReason: '',
})

const stationOptions = computed(() => {
  const names = Array.from(new Set(allOrders.value.map((item) => item.stationName)))
  return names.filter(Boolean)
})

const filteredOrders = computed(() => {
  const orderNoKw = appliedFilters.orderNo.trim().toLowerCase()
  const keyword = appliedFilters.keyword.trim().toLowerCase()
  const station = appliedFilters.stationName
  const abnormalReason = appliedFilters.abnormalReason.trim().toLowerCase()

  return allOrders.value.filter((order) => {
    const orderNoOk = !orderNoKw || order.orderNo.toLowerCase().includes(orderNoKw)
    const keywordOk =
      !keyword ||
      order.phone.toLowerCase().includes(keyword) ||
      order.userName.toLowerCase().includes(keyword)
    const stationOk = !station || order.stationName === station
    const abnormalOk = !abnormalReason || (order.abnormalReason || '').toLowerCase().includes(abnormalReason)

    return orderNoOk && keywordOk && stationOk && abnormalOk
  })
})

const total = computed(() => filteredOrders.value.length)

const tableData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredOrders.value.slice(start, start + pageSize.value)
})

const formatMoney = (value: number): string =>
  `¥${Number(value || 0).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`

const maskPhone = (phone: string): string => {
  if (!phone || phone.length < 7) return phone
  return `${phone.slice(0, 3)}****${phone.slice(-4)}`
}

const loadOrders = async () => {
  loading.value = true
  try {
    await new Promise((resolve) => {
      window.setTimeout(resolve, 120)
    })
    allOrders.value = orderStore.getAbnormalOrders()
  } finally {
    loading.value = false
  }
}

const handleSearch = async () => {
  appliedFilters.orderNo = searchForm.orderNo
  appliedFilters.keyword = searchForm.keyword
  appliedFilters.stationName = searchForm.stationName
  appliedFilters.abnormalReason = searchForm.abnormalReason
  currentPage.value = 1
  await loadOrders()
}

const handleReset = async () => {
  searchForm.orderNo = ''
  searchForm.keyword = ''
  searchForm.stationName = ''
  searchForm.abnormalReason = ''

  appliedFilters.orderNo = ''
  appliedFilters.keyword = ''
  appliedFilters.stationName = ''
  appliedFilters.abnormalReason = ''
  currentPage.value = 1

  await loadOrders()
}

const handleSizeChange = (val: number): void => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val: number): void => {
  currentPage.value = val
}

const openDetail = (row: Order): void => {
  currentOrderId.value = row.id
  drawerVisible.value = true
}

onMounted(async () => {
  await loadOrders()
  ElMessage.success('异常订单已从统一订单中心加载')
})
</script>

<template>
  <div :class="$style.page">
    <el-alert
      title="当前存在异常订单，请及时处理并复核"
      type="warning"
      show-icon
      :closable="false"
      :class="$style.alert"
    />

    <el-card shadow="never" :class="$style.filterCard">
      <el-form :model="searchForm" :class="$style.filterForm" label-width="auto">
        <div :class="$style.filterRow">
          <el-form-item label="订单号" :class="$style.formItem">
            <el-input v-model="searchForm.orderNo" placeholder="支持模糊查询" clearable style="width: 210px" />
          </el-form-item>
          <el-form-item label="手机号/用户" :class="$style.formItem">
            <el-input v-model="searchForm.keyword" placeholder="支持手机号或用户名" clearable style="width: 190px" />
          </el-form-item>
          <el-form-item label="场站" :class="$style.formItem">
            <el-select v-model="searchForm.stationName" placeholder="全部场站" clearable style="width: 200px">
              <el-option v-for="s in stationOptions" :key="s" :label="s" :value="s" />
            </el-select>
          </el-form-item>
          <el-form-item label="异常原因" :class="$style.formItem">
            <el-input v-model="searchForm.abnormalReason" placeholder="输入异常关键词" clearable style="width: 220px" />
          </el-form-item>

          <div :class="$style.actions">
            <el-button type="primary" :icon="Search" :loading="loading" @click="handleSearch">查询</el-button>
            <el-button :icon="Refresh" :disabled="loading" @click="handleReset">重置</el-button>
          </div>
        </div>
      </el-form>
    </el-card>

    <el-card shadow="never" :class="$style.tableCard">
      <el-table
        :data="tableData"
        stripe
        highlight-current-row
        :class="$style.table"
        v-loading="loading"
        element-loading-text="加载中..."
      >
        <el-table-column prop="orderNo" label="订单编号" width="190" show-overflow-tooltip />
        <el-table-column label="用户" width="110" show-overflow-tooltip>
          <template #default="{ row }">{{ row.userName }}</template>
        </el-table-column>
        <el-table-column label="手机号" width="130">
          <template #default="{ row }">{{ maskPhone(row.phone) }}</template>
        </el-table-column>
        <el-table-column prop="vin" label="VIN" width="160" show-overflow-tooltip />
        <el-table-column prop="stationName" label="电站名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="chargerName" label="电桩名称" width="160" show-overflow-tooltip />
        <el-table-column prop="startTime" label="开始时间" width="170" />
        <el-table-column prop="chargeAmount" label="充电量(kWh)" width="120" align="right">
          <template #default="{ row }">
            <span :class="$style.num">{{ Number(row.chargeAmount).toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="totalAmount" label="总金额" width="120" align="right">
          <template #default="{ row }">
            <span :class="$style.money">{{ formatMoney(row.totalAmount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="abnormalReason" label="异常原因" min-width="170" show-overflow-tooltip />
        <el-table-column label="状态" width="100" align="center">
          <template #default>
            <el-tag type="danger" effect="light">异常</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right" align="center">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div :class="$style.pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <OrderDetailDrawer v-model:visible="drawerVisible" :order="currentOrder" />
  </div>
</template>

<style module scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
}

.alert {
  border-radius: 8px;
}

.filterCard {
  border-radius: 8px;
}

.filterForm {
  width: 100%;
}

.filterRow {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.formItem {
  margin-bottom: 0;
}

.actions {
  margin-left: auto;
  display: flex;
  gap: 12px;
}

.tableCard {
  border-radius: 8px;
}

.table :deep(.el-table__header-wrapper th.el-table__cell) {
  background: #f5f7fa;
  font-size: 14px;
}

.table :deep(.el-table__row) {
  height: 48px;
}

.num {
  font-variant-numeric: tabular-nums;
}

.money {
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: #303133;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .actions {
    margin-left: 0;
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
