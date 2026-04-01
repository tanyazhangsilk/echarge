<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { VideoPlay, DataLine, Loading } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useOrderStore } from '../../stores/order'
import OrderDetailDrawer from '../../components/order/OrderDetailDrawer.vue'

const orderStore = useOrderStore()

const loading = ref(true)
const tableData = ref(orderStore.getRealtimeOrders())
const drawerVisible = ref(false)
const currentOrderId = ref('')
let refreshTimer: number | null = null

const currentOrder = computed(() => orderStore.getOrderById(currentOrderId.value) || null)

const refreshRealtimeOrders = async () => {
  loading.value = true
  try {
    await new Promise((resolve) => {
      window.setTimeout(resolve, 120)
    })
    tableData.value = orderStore.getRealtimeOrders()
  } finally {
    loading.value = false
  }
}

const stats = computed(() => ({
  active: tableData.value.length,
  totalPower: tableData.value.reduce((sum, item) => sum + Number(item.chargeAmount || 0), 0).toFixed(1),
  currentFee: tableData.value.reduce((sum, item) => sum + Number(item.totalAmount || 0), 0).toFixed(2),
}))

const handleForceStop = async (row: { id: string }) => {
  try {
    await ElMessageBox.confirm('确认强制停止该订单吗？', '强制停止', {
      confirmButtonText: '确认停止',
      cancelButtonText: '取消',
      type: 'warning',
    })
    const result = orderStore.finishOrder(row.id)
    if (!result) {
      ElMessage.warning('仅充电中订单可执行此操作')
      return
    }
    ElMessage.success('订单已结束并归档到历史订单')
    await refreshRealtimeOrders()
  } catch (error) {
    // cancel
  }
}

const handleMarkAbnormal = async (row: { id: string }) => {
  try {
    const { value } = await ElMessageBox.prompt('请输入异常原因', '标记异常', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      inputPlaceholder: '例如：充电枪中途断连',
      inputValidator: (val) => (val && val.trim().length > 0 ? true : '请填写异常原因'),
    })
    const result = orderStore.markOrderAbnormal(row.id, value)
    if (!result) {
      ElMessage.warning('仅充电中订单可执行此操作')
      return
    }
    ElMessage.success('订单已转入异常订单')
    await refreshRealtimeOrders()
  } catch (error) {
    // cancel
  }
}

const openDetail = (id: string) => {
  currentOrderId.value = id
  drawerVisible.value = true
}

onMounted(() => {
  refreshRealtimeOrders()
  refreshTimer = window.setInterval(refreshRealtimeOrders, 30000)
})

onUnmounted(() => {
  if (refreshTimer) window.clearInterval(refreshTimer)
})
</script>

<template>
  <div class="page-container">
    <div class="flex justify-between items-center mb-6">
      <div class="flex items-center gap-2">
        <div class="live-indicator"></div>
        <span class="text-gray-500 text-sm">数据实时同步中(30s刷新)</span>
      </div>
      <el-button type="primary" plain @click="refreshRealtimeOrders" :icon="Loading">手动刷新</el-button>
    </div>

    <el-row :gutter="20" class="mb-6">
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card bg-blue">
          <div class="stat-icon"><el-icon><VideoPlay /></el-icon></div>
          <div class="stat-info">
            <div class="stat-title">当前充电中车辆</div>
            <div class="stat-value">{{ stats.active }} <span class="text-sm font-normal">辆</span></div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card bg-green">
          <div class="stat-icon"><el-icon><DataLine /></el-icon></div>
          <div class="stat-info">
            <div class="stat-title">实时总输出电量</div>
            <div class="stat-value">{{ stats.totalPower }} <span class="text-sm font-normal">kWh</span></div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card bg-orange">
          <div class="stat-icon" style="font-weight: bold;">¥</div>
          <div class="stat-info">
            <div class="stat-title">当前预计总流水</div>
            <div class="stat-value">{{ stats.currentFee }} <span class="text-sm font-normal">元</span></div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="border-0 rounded-lg">
      <template #header>
        <div class="font-bold text-lg text-gray-800">实时充电监控列表</div>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="orderNo" label="订单编号" width="180">
          <template #default="scope">
            <span class="font-mono text-blue-600">{{ scope.row.orderNo }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="chargerName" label="充电终端" width="160" />
        <el-table-column prop="phone" label="用户账号" width="120" />
        <el-table-column prop="startTime" label="开始时间" width="180" />
        <el-table-column label="已充时长" width="120" align="center">
          <template #default="scope">
            <el-tag type="success" effect="plain">{{ scope.row.chargeDuration }} 分钟</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="当前电量(实时)" min-width="180">
          <template #default="scope">
            <div class="flex items-center gap-2">
              <span class="w-10 text-right">{{ scope.row.chargeAmount }}</span>
              <el-progress
                :percentage="Math.min(100, scope.row.chargeAmount * 2)"
                :show-text="false"
                class="flex-1"
                :stroke-width="8"
                striped
                striped-flow
              />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="totalAmount" label="当前金额" width="100" align="right">
          <template #default="scope">
            <strong class="text-red-500">¥{{ Number(scope.row.totalAmount).toFixed(2) }}</strong>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="scope">
            <el-button link type="primary" size="small" @click="openDetail(scope.row.id)">详情</el-button>
            <el-button link type="warning" size="small" @click="handleMarkAbnormal(scope.row)">标记异常</el-button>
            <el-button link type="danger" size="small" @click="handleForceStop(scope.row)">强制停止</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <OrderDetailDrawer v-model:visible="drawerVisible" :order="currentOrder" />
  </div>
</template>

<style scoped>
.mb-6 { margin-bottom: 24px; }
.flex { display: flex; }
.justify-between { justify-content: space-between; }
.items-center { align-items: center; }
.gap-2 { gap: 8px; }
.flex-1 { flex: 1; }
.w-10 { width: 40px; }

/* 呼吸灯动画 */
.live-indicator {
  width: 10px; height: 10px; border-radius: 50%; background-color: #67C23A;
  box-shadow: 0 0 8px #67C23A; animation: pulse 1.5s infinite;
}
@keyframes pulse {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(103, 194, 58, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(103, 194, 58, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(103, 194, 58, 0); }
}

.stat-card { border: none; color: #fff; border-radius: 8px; }
.stat-card:deep(.el-card__body) { display: flex; align-items: center; padding: 24px; }
.bg-blue { background: linear-gradient(135deg, #409EFF, #36a3f7); }
.bg-green { background: linear-gradient(135deg, #67C23A, #85ce61); }
.bg-orange { background: linear-gradient(135deg, #E6A23C, #f3d19e); }

.stat-icon { font-size: 48px; opacity: 0.8; margin-right: 20px; }
.stat-info { flex: 1; text-align: right; }
.stat-title { font-size: 14px; opacity: 0.9; margin-bottom: 4px; }
.stat-value { font-size: 32px; font-weight: bold; font-family: 'DIN Alternate', sans-serif; }
</style>
