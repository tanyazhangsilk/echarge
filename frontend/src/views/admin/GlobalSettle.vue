<script setup>
import { ref, computed, onMounted } from 'vue'
import { Money, WarningFilled, Setting, RefreshRight, DocumentChecked } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const tableData = ref([])
const loading = ref(true)

// 清分执行引擎状态
const settleDate = ref('')
const isSettling = ref(false)
const settleProgress = ref(0)
const settleLog = ref('')

// 页面加载时获取历史账单
const fetchSettlements = async () => {
  loading.value = true
  try {
    const res = await axios.get('http://127.0.0.1:8000/api/v1/admin/finance/settlements')
    if (res.data.code === 200) {
      tableData.value = res.data.data
    }
  } catch (error) {
    ElMessage.error('获取全局清分记录失败，请检查网络')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  // 默认选中昨天
  const yesterday = new Date()
  yesterday.setDate(yesterday.getDate() - 1)
  settleDate.value = yesterday.toISOString().split('T')[0]
  fetchSettlements()
})

// 顶部大盘数据计算 (基于真实返回的数据)
const stats = computed(() => {
  const totalOrders = tableData.value.reduce((sum, r) => sum + r.order_count, 0)
  const platformRevenue = tableData.value.reduce((sum, r) => sum + r.platform_fee, 0)
  const totalFlow = tableData.value.reduce((sum, r) => sum + r.total_amount, 0)
  return {
    totalOrders,
    platformRevenue: platformRevenue.toFixed(2),
    totalFlow: totalFlow.toFixed(2)
  }
})

// 执行全局清分动作
const executeSettlement = async () => {
  if (!settleDate.value) {
    ElMessage.warning('请选择需要清分的日期')
    return
  }

  await ElMessageBox.confirm(
    `即将对 ${settleDate.value} 的全网未结算订单执行 T+1 清分，并扣除 10% 平台服务费。此操作涉及资金划转，是否继续？`,
    '高危操作确认',
    { confirmButtonText: '确认执行', cancelButtonText: '取消', type: 'warning' }
  )

  isSettling.value = true
  settleProgress.value = 0
  settleLog.value = `[${new Date().toLocaleTimeString()}] 正在启动清分引擎...\n`

  // 模拟进度条效果，增加真实感
  const timer = setInterval(() => {
    if (settleProgress.value < 80) {
      settleProgress.value += Math.floor(Math.random() * 15 + 5)
      settleLog.value += `[${new Date().toLocaleTimeString()}] 正在聚合各运营商订单数据...\n`
    }
  }, 400)

  try {
    // 调用真实接口
    const res = await axios.post('http://127.0.0.1:8000/api/v1/admin/finance/settle', {
      date: settleDate.value
    })

    clearInterval(timer)
    settleProgress.value = 100
    
    if (res.data.code === 200) {
      settleLog.value += `[${new Date().toLocaleTimeString()}] 清分完成！${res.data.message}\n`
      ElMessage.success(res.data.message)
      setTimeout(() => {
        isSettling.value = false
        fetchSettlements() // 刷新下方表格
      }, 1500)
    } else {
      settleLog.value += `[${new Date().toLocaleTimeString()}] 异常: ${res.data.message}\n`
      ElMessage.error(res.data.message)
      isSettling.value = false
    }
  } catch (error) {
    clearInterval(timer)
    isSettling.value = false
    settleLog.value += `[${new Date().toLocaleTimeString()}] 引擎连接失败！\n`
    ElMessage.error('执行失败，请检查后端服务是否启动')
  }
}
</script>

<template>
  <div class="page-container">
    <el-alert 
      title="清分中心具有最高财务权限。T+1 清分将自动计算全网昨日流水，划扣平台服务费(10%)，并生成运营商可提现账单。" 
      type="warning" 
      show-icon 
      class="mb-6 py-2" 
      :closable="false"
    />

    <el-row :gutter="20" class="mb-6">
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card bg-gradient-dark">
          <div class="stat-icon"><el-icon><Money /></el-icon></div>
          <div class="stat-info">
            <div class="stat-title text-gray-300">累计平台抽成收益 (元)</div>
            <div class="stat-value text-white">￥{{ stats.platformRevenue }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card border-l-blue">
          <div class="stat-info">
            <div class="stat-title">全网历史总流水 (元)</div>
            <div class="stat-value text-blue-600">￥{{ stats.totalFlow }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card border-l-green">
          <div class="stat-info">
            <div class="stat-title">累计清分处理订单 (笔)</div>
            <div class="stat-value text-green-600">{{ stats.totalOrders }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="engine-card mb-6 border-0 rounded-lg">
      <template #header>
        <div class="font-bold text-lg flex items-center">
          <el-icon class="mr-2 text-blue-500"><Setting /></el-icon> 资金清分执行引擎
        </div>
      </template>

      <div class="engine-control flex items-center gap-6" v-if="!isSettling">
        <div class="flex items-center gap-4">
          <span class="text-gray-600 font-medium">选择清分日期:</span>
          <el-date-picker 
            v-model="settleDate" 
            type="date" 
            placeholder="选择日期" 
            format="YYYY/MM/DD" 
            value-format="YYYY-MM-DD"
            :clearable="false"
            style="width: 180px;"
          />
        </div>
        <el-button type="primary" size="large" :icon="RefreshRight" @click="executeSettlement" class="execute-btn">
          立即执行全网清分
        </el-button>
        <span class="text-sm text-gray-400"><el-icon><WarningFilled /></el-icon> 建议每天凌晨自动执行，此处为人工干预入口</span>
      </div>

      <div v-else class="engine-progress">
        <div class="flex justify-between mb-2 text-sm text-gray-600 font-bold">
          <span>引擎高速运转中...</span>
          <span>{{ settleProgress }}%</span>
        </div>
        <el-progress :percentage="settleProgress" :stroke-width="14" striped striped-flow color="#409EFF" :show-text="false" />
        <div class="console-log mt-4">
          <pre>{{ settleLog }}</pre>
        </div>
      </div>
    </el-card>

    <el-card shadow="never" class="border-0 rounded-lg">
      <template #header>
        <div class="font-bold text-lg flex items-center">
          <el-icon class="mr-2 text-gray-500"><DocumentChecked /></el-icon> 历史清分批次明细
        </div>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe border style="width: 100%" :header-cell-style="{ background: '#f8f9fa' }">
        <el-table-column prop="settle_date" label="清分归属日期" width="160" align="center">
          <template #default="scope">
            <strong class="text-gray-800">{{ scope.row.settle_date }}</strong>
          </template>
        </el-table-column>
        <el-table-column prop="order_count" label="打包订单数" width="120" align="center" />
        <el-table-column prop="total_amount" label="全网总流水 (总充值)" min-width="160" align="right">
          <template #default="scope">
            <span class="text-gray-600">￥{{ scope.row.total_amount.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="platform_fee" label="平台截留抽成 (10%)" min-width="160" align="right">
          <template #default="scope">
            <strong class="text-red-500">￥{{ scope.row.platform_fee.toFixed(2) }}</strong>
          </template>
        </el-table-column>
        <el-table-column prop="settle_amount" label="下发运营商总额" min-width="160" align="right">
          <template #default="scope">
            <strong class="text-green-600">￥{{ scope.row.settle_amount.toFixed(2) }}</strong>
          </template>
        </el-table-column>
        <el-table-column label="批次状态" width="120" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.status === 1 ? 'success' : 'warning'" effect="dark">
              {{ scope.row.status === 1 ? '入账成功' : '处理中' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right" align="center">
          <template #default="scope">
            <el-button link type="primary" size="small">查看财报</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.page-container { display: flex; flex-direction: column; }
.mb-6 { margin-bottom: 24px; }
.mt-4 { margin-top: 16px; }
.py-2 { padding-top: 8px; padding-bottom: 8px; }
.mr-2 { margin-right: 8px; }
.flex { display: flex; }
.items-center { align-items: center; }
.justify-between { justify-content: space-between; }
.gap-4 { gap: 16px; }
.gap-6 { gap: 24px; }

/* 顶部卡片样式 */
.stat-card { border: none; border-radius: 8px; height: 120px; }
.stat-card:deep(.el-card__body) { display: flex; align-items: center; padding: 24px; height: 100%; box-sizing: border-box; }
.bg-gradient-dark { background: linear-gradient(135deg, #1e293b, #334155); }
.border-l-blue { border-left: 4px solid #409EFF; }
.border-l-green { border-left: 4px solid #67C23A; }

.stat-icon { font-size: 54px; opacity: 0.2; color: #fff; margin-right: 20px; }
.stat-info { flex: 1; }
.stat-title { font-size: 14px; margin-bottom: 8px; font-weight: 500; color: #909399; }
.stat-value { font-size: 32px; font-weight: bold; font-family: 'DIN Alternate', sans-serif; }

.text-gray-300 { color: #cbd5e1; }
.text-gray-400 { color: #94a3b8; }
.text-gray-500 { color: #64748b; }
.text-gray-600 { color: #475569; }
.text-gray-800 { color: #1e293b; }
.text-white { color: #ffffff; }
.text-blue-500 { color: #3b82f6; }
.text-blue-600 { color: #2563eb; }
.text-green-600 { color: #16a34a; }
.text-red-500 { color: #ef4444; }

/* 引擎控制台 */
.engine-card { background: #f8fafc; border: 1px solid #e2e8f0; }
.execute-btn { background: linear-gradient(135deg, #3b82f6, #2563eb); border: none; box-shadow: 0 4px 14px rgba(37, 99, 235, 0.3); font-weight: bold; letter-spacing: 1px; }
.execute-btn:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(37, 99, 235, 0.4); }

/* 控制台日志打印区 */
.console-log {
  background-color: #1e293b;
  border-radius: 6px;
  padding: 12px;
  height: 120px;
  overflow-y: auto;
}
.console-log pre {
  margin: 0;
  color: #10b981; /* 荧光绿终端字色 */
  font-family: 'Courier New', Courier, monospace;
  font-size: 13px;
  line-height: 1.6;
}
</style>