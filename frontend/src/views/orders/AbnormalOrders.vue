<script setup>
import { ref, onMounted } from 'vue'
import { Warning, Search, Check } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '../../api/http'

const tableData = ref([])
const loading = ref(true)
const searchQuery = ref('')

const fetchData = async () => {
  loading.value = true
  try {
    const res = await http.get('/orders/abnormal')
    if (res.data.code === 200) {
      tableData.value = res.data.data
    }
  } catch (error) {
    ElMessage.error('获取异常订单失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
})

const handleOrder = (row) => {
  ElMessageBox.confirm(
    `确认将订单 ${row.order_no} 标记为已处理？此操作通常伴随退款或客诉完结。`,
    '处理异常订单',
    { confirmButtonText: '标记已处理', cancelButtonText: '取消', type: 'warning' }
  ).then(() => {
    row.handle_status = 1
    ElMessage.success('订单处理状态已更新')
  }).catch(() => {})
}
</script>

<template>
  <div class="page-container">
    <el-alert 
      title="警告：您有待处理的异常订单！请尽快介入处理以避免客诉。" 
      type="error" 
      show-icon 
      class="mb-6 py-2"
      :closable="false"
    />

    <el-card shadow="never" class="border-0 rounded-lg">
      <div class="flex justify-between items-center mb-6">
        <div class="flex gap-4">
          <el-input v-model="searchQuery" placeholder="搜索订单号或手机号..." :prefix-icon="Search" style="width: 260px;" />
          <el-select placeholder="异常原因过滤" style="width: 180px;">
            <el-option label="全部异常" value="" />
            <el-option label="设备离线断电" value="1" />
            <el-option label="通讯心跳超时" value="2" />
          </el-select>
          <el-select placeholder="处理状态" style="width: 140px;">
            <el-option label="全部" value="" />
            <el-option label="未处理" value="0" />
            <el-option label="已处理" value="1" />
          </el-select>
          <el-button type="primary">查询</el-button>
        </div>
      </div>

      <el-table :data="tableData" v-loading="loading" stripe border style="width: 100%" :header-cell-style="{ background: '#fef0f0', color: '#F56C6C' }">
        <el-table-column prop="order_no" label="异常订单号" width="200">
          <template #default="scope">
            <span class="font-mono text-gray-700">{{ scope.row.order_no }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="start_time" label="发生时间" width="180" />
        <el-table-column prop="user_phone" label="受影响用户" width="120" />
        <el-table-column prop="charger_sn" label="故障终端" width="140" />
        <el-table-column prop="error_reason" label="系统诊断原因" min-width="180">
          <template #default="scope">
            <el-tag type="danger" effect="light" class="w-full justify-start">
              <el-icon class="mr-1"><Warning /></el-icon>{{ scope.row.error_reason }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_fee" label="涉及金额" width="100" align="right">
          <template #default="scope">
            <strong class="text-gray-800">￥{{ scope.row.total_fee }}</strong>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.handle_status === 0 ? 'warning' : 'success'" effect="dark">
              {{ scope.row.handle_status === 0 ? '待介入' : '已解决' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="人工干预" width="180" fixed="right">
          <template #default="scope">
            <el-button 
              size="small" 
              :type="scope.row.handle_status === 0 ? 'primary' : 'default'"
              :disabled="scope.row.handle_status === 1"
              @click="handleOrder(scope.row)"
            >
              {{ scope.row.handle_status === 0 ? '立即处理' : '查看记录' }}
            </el-button>
            <el-button v-if="scope.row.handle_status === 0" size="small" type="danger" plain>退款</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="flex justify-end mt-6">
        <el-pagination background layout="prev, pager, next" :total="tableData.length" />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.mb-6 { margin-bottom: 24px; }
.mt-6 { margin-top: 24px; }
.py-2 { padding-top: 8px; padding-bottom: 8px; }
.flex { display: flex; }
.justify-between { justify-content: space-between; }
.justify-end { justify-content: flex-end; }
.items-center { align-items: center; }
.gap-4 { gap: 16px; }
.w-full { width: 100%; display: flex; }
.mr-1 { margin-right: 4px; }

.text-gray-700 { color: #606266; }
.text-gray-800 { color: #303133; }
.font-mono { font-family: monospace; }
</style>
