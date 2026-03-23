<script setup>
import { ref, computed, onMounted } from 'vue'
import { Search, UploadFilled, Document, Check, Close, Message } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '../../api/http'

const tableData = ref([])
const loading = ref(true)

// 顶部统计
const stats = computed(() => {
  const pending = tableData.value.filter(i => i.status === 0).length
  const completed = tableData.value.filter(i => i.status === 1)
  const totalAmount = completed.reduce((sum, i) => sum + i.amount, 0)
  return { pending, completedCount: completed.length, totalAmount: totalAmount.toFixed(2) }
})

const fetchInvoices = async () => {
  loading.value = true
  try {
    const res = await http.get('/finance/invoices')
    if (res.data.code === 200) {
      tableData.value = res.data.data
    }
  } catch (error) {
    ElMessage.error('获取发票列表失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchInvoices()
})

// --- 处理开票交互逻辑 ---
const processDialogVisible = ref(false)
const currentInvoice = ref(null)
const uploadProgress = ref(0)
const isUploading = ref(false)
const uploadedFile = ref('')

const openProcessDialog = (row) => {
  currentInvoice.value = row
  uploadedFile.value = ''
  uploadProgress.value = 0
  isUploading.value = false
  processDialogVisible.value = true
}

// 模拟假装上传文件的酷炫过程
const simulateUpload = () => {
  isUploading.value = true
  uploadProgress.value = 0
  const interval = setInterval(() => {
    uploadProgress.value += Math.floor(Math.random() * 15 + 5)
    if (uploadProgress.value >= 100) {
      uploadProgress.value = 100
      clearInterval(interval)
      setTimeout(() => {
        isUploading.value = false
        uploadedFile.value = 'https://echarge-system.com/invoices/INV_auto_gen.pdf'
        ElMessage.success('发票文件解析上传成功')
      }, 500)
    }
  }, 200)
}

const submitProcess = async (action) => {
  if (action === 'approve' && !uploadedFile.value) {
    ElMessage.warning('请先上传发票文件')
    return
  }
  
  const confirmText = action === 'approve' ? '确认向该用户发送电子发票？' : '确认驳回该用户的开票申请？'
  
  try {
    await ElMessageBox.confirm(confirmText, '操作确认', { type: action === 'approve' ? 'success' : 'warning' })
    
    const res = await http.post(`/finance/invoices/${currentInvoice.value.id}/process`, {
      action: action,
      file_url: uploadedFile.value
    })
    
    if (res.data.code === 200) {
      ElMessage.success(action === 'approve' ? '开票成功，已通过邮件发送给用户' : '已驳回申请')
      processDialogVisible.value = false
      fetchInvoices() // 刷新列表
    }
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('处理失败')
  }
}

const getStatusType = (status) => {
  if (status === 0) return 'warning'
  if (status === 1) return 'success'
  return 'danger'
}
const getStatusText = (status) => {
  if (status === 0) return '待开票'
  if (status === 1) return '已开票'
  return '已驳回'
}
</script>

<template>
  <div class="page-container">
    <el-row :gutter="20" class="mb-6">
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card border-l-orange">
          <div class="stat-icon-bg bg-orange-light"><el-icon color="#E6A23C"><Document /></el-icon></div>
          <div class="stat-info">
            <div class="stat-title">待处理开票申请</div>
            <div class="stat-value text-orange">{{ stats.pending }} <span class="unit">笔</span></div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card border-l-blue">
          <div class="stat-icon-bg bg-blue-light"><el-icon color="#409EFF"><Message /></el-icon></div>
          <div class="stat-info">
            <div class="stat-title">已成功开具</div>
            <div class="stat-value text-blue">{{ stats.completedCount }} <span class="unit">笔</span></div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card border-l-green">
          <div class="stat-icon-bg bg-green-light"><span style="color: #67C23A; font-weight: bold; font-size: 24px;">￥</span></div>
          <div class="stat-info">
            <div class="stat-title">累计开票金额</div>
            <div class="stat-value text-green">{{ stats.totalAmount }} <span class="unit">元</span></div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="main-card">
      <template #header>
        <div class="font-bold text-lg text-gray-800">用户发票开具管理</div>
      </template>

      <div class="action-bar mb-6 flex justify-between">
        <div class="flex gap-4">
          <el-input placeholder="搜索申请单号、邮箱..." :prefix-icon="Search" style="width: 240px" />
          <el-select placeholder="处理状态" style="width: 150px">
            <el-option label="全部状态" value="" />
            <el-option label="待开票" value="0" />
            <el-option label="已开票" value="1" />
            <el-option label="已驳回" value="2" />
          </el-select>
          <el-button type="primary" plain>筛选</el-button>
        </div>
        <el-button type="primary">批量导出记录</el-button>
      </div>

      <el-table :data="tableData" v-loading="loading" stripe style="width: 100%" :header-cell-style="{ background: '#f8f9fa' }">
        <el-table-column prop="invoice_no" label="申请单号" width="180">
          <template #default="scope">
            <span class="font-mono">{{ scope.row.invoice_no }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="申请时间" width="170" />
        <el-table-column prop="user_phone" label="申请用户手机" width="130" />
        <el-table-column prop="email" label="接收邮箱" min-width="180">
          <template #default="scope">
            <el-link type="primary" :underline="false">{{ scope.row.email }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="开票金额" width="120" align="right">
          <template #default="scope">
            <strong class="text-lg text-gray-800">￥{{ scope.row.amount.toFixed(2) }}</strong>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)" effect="dark" round size="small">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="scope">
            <el-button 
              v-if="scope.row.status === 0" 
              type="primary" 
              size="small" 
              @click="openProcessDialog(scope.row)"
            >
              处理开票
            </el-button>
            <el-button v-else link type="info" size="small">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="processDialogVisible" title="开具电子发票" width="550px">
      <div v-if="currentInvoice" class="invoice-summary mb-6">
        <div class="summary-item">
          <span>申请单号：</span><strong>{{ currentInvoice.invoice_no }}</strong>
        </div>
        <div class="summary-item">
          <span>接收邮箱：</span><strong>{{ currentInvoice.email }}</strong>
        </div>
        <div class="summary-item">
          <span>开票金额：</span><strong style="color: #F56C6C; font-size: 18px;">￥{{ currentInvoice.amount.toFixed(2) }}</strong>
        </div>
      </div>

      <div class="upload-area" @click="simulateUpload" v-if="!uploadedFile && !isUploading">
        <el-icon class="upload-icon"><UploadFilled /></el-icon>
        <div class="upload-text">点击或拖拽发票文件 (PDF/JPG) 至此</div>
      </div>

      <div v-if="isUploading" class="upload-progress">
        <span style="font-size: 13px; color: #606266; margin-bottom: 8px;">文件解析上传中...</span>
        <el-progress :percentage="uploadProgress" :stroke-width="10" striped striped-flow />
      </div>

      <div v-if="uploadedFile" class="upload-success">
        <el-icon color="#67C23A" :size="24" class="mr-2"><Check /></el-icon>
        <span>发票文件已就绪 (INV_auto_gen.pdf)</span>
        <el-button link type="danger" @click="uploadedFile = ''" style="margin-left: auto;">重新上传</el-button>
      </div>

      <template #footer>
        <div class="flex justify-between w-full items-center">
          <el-button type="danger" plain @click="submitProcess('reject')" :icon="Close">驳回申请</el-button>
          <div>
            <el-button @click="processDialogVisible = false">暂不处理</el-button>
            <el-button type="primary" @click="submitProcess('approve')" :disabled="!uploadedFile">确认开出并发邮件</el-button>
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.mb-6 { margin-bottom: 24px; }
.flex { display: flex; }
.justify-between { justify-content: space-between; }
.items-center { align-items: center; }
.w-full { width: 100%; }
.gap-4 { gap: 16px; }
.mr-2 { margin-right: 8px; }

/* 统计卡片样式 */
.stat-card { border: none; border-radius: 8px; }
.stat-card:deep(.el-card__body) { display: flex; align-items: center; padding: 20px; }
.stat-icon-bg { width: 48px; height: 48px; border-radius: 12px; display: flex; justify-content: center; align-items: center; font-size: 24px; margin-right: 16px; }
.stat-info { flex: 1; }
.stat-title { font-size: 13px; color: #909399; margin-bottom: 4px; }
.stat-value { font-size: 28px; font-weight: bold; font-family: 'DIN Alternate', sans-serif; }
.unit { font-size: 13px; font-weight: normal; }

/* 边框与颜色 */
.border-l-orange { border-left: 4px solid #E6A23C; }
.border-l-blue { border-left: 4px solid #409EFF; }
.border-l-green { border-left: 4px solid #67C23A; }
.bg-orange-light { background-color: #fdf6ec; }
.bg-blue-light { background-color: #ecf5ff; }
.bg-green-light { background-color: #f0f9eb; }
.text-orange { color: #E6A23C; }
.text-blue { color: #409EFF; }
.text-green { color: #67C23A; }

.main-card { border: none; border-radius: 8px; }
.font-mono { font-family: monospace; color: #606266; }
.text-lg { font-size: 16px; }

/* 弹窗内的样式 */
.invoice-summary { background: #f8f9fa; padding: 16px; border-radius: 6px; border: 1px solid #ebeef5; }
.summary-item { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 14px; }
.summary-item:last-child { margin-bottom: 0; }
.summary-item span { color: #909399; }
.summary-item strong { color: #303133; }

.upload-area { border: 2px dashed #dcdfe6; border-radius: 8px; padding: 32px 0; text-align: center; cursor: pointer; transition: all 0.3s; background: #fafafa; }
.upload-area:hover { border-color: #409EFF; background: #ecf5ff; }
.upload-icon { font-size: 48px; color: #c0c4cc; margin-bottom: 12px; }
.upload-text { font-size: 14px; color: #606266; }

.upload-progress { display: flex; flex-direction: column; padding: 20px 0; }
.upload-success { display: flex; align-items: center; background: #f0f9eb; border: 1px solid #e1f3d8; padding: 16px; border-radius: 8px; color: #67C23A; font-weight: 500; }
</style>
