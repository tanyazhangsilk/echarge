<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Search } from '@element-plus/icons-vue'

type OrderStatus = 'completed' | 'abnormal' | 'refund'

interface Order {
  orderNo: string
  startTime: string
  endTime: string
  userName: string
  userPhone: string
  stationName: string
  kwh: number
  amount: number
  status: OrderStatus
  vin: string
  gunNo: string
}

interface FilterForm {
  orderNo: string
  phone: string
  stationName: string
  dateRange: [Date, Date] | []
  status: OrderStatus | ''
}

const stationOptions = [
  '南山科技园充电站',
  '福田市民中心充电站',
  '宝安国际机场充电站',
  '中心广场充电站',
  '前海自贸区示范站',
  '光明科学城综合站',
]

const now = new Date()
const defaultEnd = new Date(now)
const defaultStart = new Date(now)
defaultStart.setDate(defaultStart.getDate() - 30)

// 高级筛选表单 / Advanced filter form
const searchForm = reactive<FilterForm>({
  orderNo: '',
  phone: '',
  stationName: '',
  dateRange: [defaultStart, defaultEnd],
  status: '',
})

// 已应用筛选 / Applied filters (only changes on Query/Reset)
const appliedFilters = reactive<FilterForm>({
  orderNo: '',
  phone: '',
  stationName: '',
  dateRange: [defaultStart, defaultEnd],
  status: '',
})

// 数据源 / Data source
const allOrders = ref<Order[]>([])
const loading = ref(false)

// 分页 / Pagination
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)

// 抽屉 / Drawer
const drawerVisible = ref(false)
const currentOrder = ref<Order | null>(null)

/**
 * 金额格式化 / Format money with thousand separators
 */
const formatMoney = (value: number): string => {
  const num = Number(value)
  const formatter = new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
  return `￥${formatter.format(Number.isFinite(num) ? num : 0)}`
}

/**
 * 时间格式化 / Format date to yyyy-MM-dd HH:mm:ss
 */
const formatDateTime = (value: Date): string => {
  const pad2 = (n: number) => String(n).padStart(2, '0')
  const y = value.getFullYear()
  const m = pad2(value.getMonth() + 1)
  const d = pad2(value.getDate())
  const hh = pad2(value.getHours())
  const mm = pad2(value.getMinutes())
  const ss = pad2(value.getSeconds())
  return `${y}-${m}-${d} ${hh}:${mm}:${ss}`
}

/**
 * 手机号脱敏 / Mask phone number
 */
const maskPhone = (phone: string): string => {
  const s = String(phone || '')
  if (s.length < 7) return s
  return `${s.slice(0, 3)}****${s.slice(-4)}`
}

/**
 * 生成 VIN 码 / Generate VIN (17 chars)
 */
const generateVin = (): string => {
  const chars = 'ABCDEFGHJKLMNPRSTUVWXYZ0123456789'
  let out = ''
  for (let i = 0; i < 17; i += 1) {
    out += chars[Math.floor(Math.random() * chars.length)]
  }
  return out
}

/**
 * 生成订单号 / Generate order number
 */
const generateOrderNo = (): string => {
  const pad = (n: number, len: number) => String(n).padStart(len, '0')
  const d = new Date()
  const y = d.getFullYear()
  const m = pad(d.getMonth() + 1, 2)
  const day = pad(d.getDate(), 2)
  const rand = pad(Math.floor(Math.random() * 1e8), 8)
  return `CD${y}${m}${day}${rand}`
}

/**
 * Mock 数据生成器 / Mock data generator
 * @param count 数量 / count
 */
const generateMockOrders = (count: number): Order[] => {
  const names = ['张伟', '王芳', '李娜', '刘强', '陈涛', '赵敏', '孙鹏', '周倩', '吴磊', '郑爽']
  const phones = ['13800135678', '13912345678', '13798765432', '13622223333', '13566667777', '18800001111']
  const statuses: OrderStatus[] = ['completed', 'abnormal', 'refund']
  const results: Order[] = []

  for (let i = 0; i < count; i += 1) {
    const stationName = stationOptions[i % stationOptions.length]
    const userName = names[Math.floor(Math.random() * names.length)]
    const userPhone = phones[Math.floor(Math.random() * phones.length)]
    const status = statuses[Math.floor(Math.random() * statuses.length)]

    const start = new Date()
    start.setDate(start.getDate() - Math.floor(Math.random() * 30))
    start.setHours(Math.floor(Math.random() * 24), Math.floor(Math.random() * 60), Math.floor(Math.random() * 60), 0)
    const durationMin = 20 + Math.floor(Math.random() * 200)
    const end = new Date(start.getTime() + durationMin * 60 * 1000)

    const kwh = Number((5 + Math.random() * 65).toFixed(2))
    const amount = Number((kwh * (0.9 + Math.random() * 0.9)).toFixed(2))

    results.push({
      orderNo: generateOrderNo(),
      startTime: formatDateTime(start),
      endTime: formatDateTime(end),
      userName,
      userPhone,
      stationName,
      kwh,
      amount,
      status,
      vin: generateVin(),
      gunNo: `枪-${String(1 + (i % 12)).padStart(2, '0')}`,
    })
  }

  results.sort((a, b) => (a.startTime < b.startTime ? 1 : -1))
  return results
}

/**
 * 状态标签 / Status tag mapping
 */
const statusTag = (status: OrderStatus): { type: 'success' | 'danger' | 'warning'; text: string } => {
  if (status === 'completed') return { type: 'success', text: '已完成' }
  if (status === 'abnormal') return { type: 'danger', text: '充电异常' }
  return { type: 'warning', text: '退款' }
}

const filteredOrders = computed(() => {
  const orderNoKw = appliedFilters.orderNo.trim()
  const phoneKw = appliedFilters.phone.trim()
  const station = appliedFilters.stationName
  const status = appliedFilters.status
  const range = appliedFilters.dateRange

  return allOrders.value.filter((o) => {
    const orderNoOk = !orderNoKw || o.orderNo.includes(orderNoKw)
    const phoneOk = !phoneKw || o.userPhone.includes(phoneKw)
    const stationOk = !station || o.stationName === station
    const statusOk = !status || o.status === status

    let dateOk = true
    if (Array.isArray(range) && range.length === 2) {
      const [start, end] = range
      const s = start.getTime()
      const e = end.getTime()
      const t = new Date(o.startTime).getTime()
      dateOk = t >= s && t <= e + 24 * 60 * 60 * 1000 - 1
    }

    return orderNoOk && phoneOk && stationOk && statusOk && dateOk
  })
})

const tableData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredOrders.value.slice(start, start + pageSize.value)
})

/**
 * 模拟请求 / Simulate request with 300ms delay
 */
const fetchOrders = async (): Promise<void> => {
  loading.value = true
  try {
    await new Promise<void>((resolve) => {
      setTimeout(() => resolve(), 300)
    })
    allOrders.value = generateMockOrders(16)
    total.value = filteredOrders.value.length
    currentPage.value = 1
  } finally {
    loading.value = false
  }
}

const handleSearch = async (): Promise<void> => {
  appliedFilters.orderNo = searchForm.orderNo
  appliedFilters.phone = searchForm.phone
  appliedFilters.stationName = searchForm.stationName
  appliedFilters.status = searchForm.status
  appliedFilters.dateRange = Array.isArray(searchForm.dateRange) && searchForm.dateRange.length === 2 ? [...searchForm.dateRange] : []
  await fetchOrders()
}

const handleReset = async (): Promise<void> => {
  searchForm.orderNo = ''
  searchForm.phone = ''
  searchForm.stationName = ''
  searchForm.status = ''
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - 30)
  searchForm.dateRange = [start, end]

  appliedFilters.orderNo = ''
  appliedFilters.phone = ''
  appliedFilters.stationName = ''
  appliedFilters.status = ''
  appliedFilters.dateRange = [start, end]
  await fetchOrders()
}

const handleSizeChange = (val: number): void => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val: number): void => {
  currentPage.value = val
}

const openDetail = (row: Order): void => {
  currentOrder.value = row
  drawerVisible.value = true
}

const closeDrawer = (): void => {
  drawerVisible.value = false
}

onMounted(async () => {
  appliedFilters.orderNo = searchForm.orderNo
  appliedFilters.phone = searchForm.phone
  appliedFilters.stationName = searchForm.stationName
  appliedFilters.status = searchForm.status
  appliedFilters.dateRange = Array.isArray(searchForm.dateRange) && searchForm.dateRange.length === 2 ? [...searchForm.dateRange] : []
  await fetchOrders()
  ElMessage.success('已加载最近 30 天历史订单')
})
</script>

<template>
  <div :class="$style.page">
    <el-card shadow="never" :class="$style.filterCard">
      <el-form :model="searchForm" :class="$style.filterForm" label-width="auto">
        <div :class="$style.filterRow">
          <el-form-item label="订单号" :class="$style.formItem">
            <el-input v-model="searchForm.orderNo" placeholder="支持模糊查询" clearable style="width: 210px" />
          </el-form-item>
          <el-form-item label="手机号" :class="$style.formItem">
            <el-input v-model="searchForm.phone" placeholder="支持模糊查询" clearable style="width: 190px" />
          </el-form-item>
          <el-form-item label="电站" :class="$style.formItem">
            <el-select v-model="searchForm.stationName" placeholder="全部电站" clearable style="width: 200px">
              <el-option v-for="s in stationOptions" :key="s" :label="s" :value="s" />
            </el-select>
          </el-form-item>
          <el-form-item label="时间范围" :class="$style.formItem">
            <el-date-picker
              v-model="searchForm.dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始"
              end-placeholder="结束"
              style="width: 320px"
            />
          </el-form-item>
          <el-form-item label="状态" :class="$style.formItem">
            <el-select v-model="searchForm.status" placeholder="全部状态" clearable style="width: 150px">
              <el-option label="已完成" value="completed" />
              <el-option label="充电异常" value="abnormal" />
              <el-option label="退款" value="refund" />
            </el-select>
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
        <el-table-column prop="startTime" label="开始时间" width="170" />
        <el-table-column prop="endTime" label="结束时间" width="170" />
        <el-table-column label="用户" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <span>{{ row.userName }}（{{ maskPhone(row.userPhone) }}）</span>
          </template>
        </el-table-column>
        <el-table-column prop="stationName" label="所属电站" min-width="180" show-overflow-tooltip />
        <el-table-column prop="kwh" label="充电量(kWh)" width="120" align="right">
          <template #default="{ row }">
            <span :class="$style.num">{{ row.kwh.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="订单金额" width="140" align="right">
          <template #default="{ row }">
            <span :class="$style.money">{{ formatMoney(row.amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status).type">{{ statusTag(row.status).text }}</el-tag>
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

    <el-drawer
      v-model="drawerVisible"
      :with-header="true"
      :close-on-click-modal="true"
      direction="rtl"
      size="50%"
    >
      <template #header>
        <div :class="$style.drawerTitle">
          订单详情{{ currentOrder?.orderNo?.slice(-6) || '' }}
        </div>
      </template>

      <div v-if="currentOrder" :class="$style.drawerBody">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="订单编号">{{ currentOrder.orderNo }}</el-descriptions-item>
          <el-descriptions-item label="车辆 VIN 码">{{ currentOrder.vin }}</el-descriptions-item>
          <el-descriptions-item label="枪头编号">{{ currentOrder.gunNo }}</el-descriptions-item>
          <el-descriptions-item label="结束原因">用户主动拔枪</el-descriptions-item>
          <el-descriptions-item label="开始时间">{{ currentOrder.startTime }}</el-descriptions-item>
          <el-descriptions-item label="结束时间">{{ currentOrder.endTime }}</el-descriptions-item>
          <el-descriptions-item label="充电量">{{ currentOrder.kwh.toFixed(2) }} kWh</el-descriptions-item>
          <el-descriptions-item label="订单金额">{{ formatMoney(currentOrder.amount) }}</el-descriptions-item>
        </el-descriptions>

        <div :class="$style.drawerFooter">
          <el-button @click="closeDrawer">关闭</el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<style module scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
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

.drawerTitle {
  font-weight: 700;
  color: #409eff;
}

.drawerBody {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.drawerFooter {
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
