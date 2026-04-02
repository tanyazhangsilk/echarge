<script setup>
import { computed, onMounted, ref } from 'vue'
import { Search, UploadFilled, Document, Check, Close, Message, Download, RefreshRight } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import EmptyStateBlock from '../../components/console/EmptyStateBlock.vue'
import http from '../../api/http'

const tableData = ref([])
const loading = ref(true)

const keyword = ref('')
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(10)

const filteredRows = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  return tableData.value.filter((item) => {
    const statusOk = statusFilter.value === '' ? true : String(item.status) === statusFilter.value
    const keywordOk =
      !kw ||
      String(item.invoice_no || '').toLowerCase().includes(kw) ||
      String(item.user_phone || '').toLowerCase().includes(kw) ||
      String(item.email || '').toLowerCase().includes(kw)
    return statusOk && keywordOk
  })
})

const pagedRows = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredRows.value.slice(start, start + pageSize.value)
})

const stats = computed(() => {
  const pending = tableData.value.filter((i) => Number(i.status) === 0).length
  const completed = tableData.value.filter((i) => Number(i.status) === 1)
  const rejected = tableData.value.filter((i) => Number(i.status) === 2).length
  const totalAmount = completed.reduce((sum, i) => sum + Number(i.amount || 0), 0)
  return {
    pending,
    completedCount: completed.length,
    rejected,
    totalAmount,
  }
})

const statCards = computed(() => [
  {
    label: '待处理开票申请',
    value: stats.value.pending,
    suffix: ' 笔',
    trend: '需要财务处理',
    trendLabel: '建议优先处理超时申请',
    tone: 'warning',
    icon: Document,
  },
  {
    label: '已成功开具',
    value: stats.value.completedCount,
    suffix: ' 笔',
    trend: '已发送至用户邮箱',
    trendLabel: '支持后续开票留档',
    tone: 'success',
    icon: Message,
  },
  {
    label: '累计开票金额',
    value: Number(stats.value.totalAmount).toFixed(2),
    prefix: '¥',
    trend: '已开票金额汇总',
    trendLabel: '按状态=已开具统计',
    tone: 'primary',
    icon: Download,
  },
  {
    label: '已驳回申请',
    value: stats.value.rejected,
    suffix: ' 笔',
    trend: '待用户补资料',
    trendLabel: '需给出驳回原因',
    tone: 'danger',
    icon: Close,
  },
])

const fetchInvoices = async () => {
  loading.value = true
  try {
    const res = await http.get('/finance/invoices')
    if (res.data.code === 200) {
      tableData.value = Array.isArray(res.data.data) ? res.data.data : []
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

const simulateUpload = () => {
  isUploading.value = true
  uploadProgress.value = 0
  const interval = setInterval(() => {
    uploadProgress.value += Math.floor(Math.random() * 15 + 6)
    if (uploadProgress.value >= 100) {
      uploadProgress.value = 100
      clearInterval(interval)
      setTimeout(() => {
        isUploading.value = false
        uploadedFile.value = 'https://echarge-system.com/invoices/INV_auto_gen.pdf'
        ElMessage.success('发票文件上传成功')
      }, 400)
    }
  }, 180)
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
      action,
      file_url: uploadedFile.value,
    })

    if (res.data.code === 200) {
      ElMessage.success(action === 'approve' ? '开票成功，已发送至用户邮箱' : '已驳回申请')
      processDialogVisible.value = false
      fetchInvoices()
    }
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('处理失败')
  }
}

const getStatusType = (status) => {
  if (Number(status) === 0) return 'warning'
  if (Number(status) === 1) return 'success'
  return 'danger'
}

const getStatusText = (status) => {
  if (Number(status) === 0) return '待开票'
  if (Number(status) === 1) return '已开具'
  return '已驳回'
}

const resetFilters = () => {
  keyword.value = ''
  statusFilter.value = ''
  currentPage.value = 1
}

const exportRows = () => {
  if (!filteredRows.value.length) {
    ElMessage.warning('当前无可导出数据')
    return
  }

  const headers = ['申请单号', '申请时间', '用户手机号', '邮箱', '金额', '状态']
  const lines = [headers.join(',')]
  filteredRows.value.forEach((item) => {
    const row = [
      item.invoice_no,
      item.created_at,
      item.user_phone,
      item.email,
      Number(item.amount || 0).toFixed(2),
      getStatusText(item.status),
    ]
    lines.push(row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(','))
  })

  const csvContent = `\uFEFF${lines.join('\n')}`
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `发票管理_${new Date().toISOString().slice(0, 10)}.csv`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}
</script>

<template>
  <div class="page-shell invoice-management-page">
    <PageSectionHeader
      eyebrow="Invoice Management"
      title="开票管理"
      description="处理运营商用户开票申请，支持审核、上传电子发票并发送回执。"
      chip="运营商财务模块"
    >
      <template #actions>
        <el-button :icon="RefreshRight" @click="fetchInvoices">刷新</el-button>
        <el-button type="primary" :icon="Download" @click="exportRows">导出记录</el-button>
      </template>
    </PageSectionHeader>

    <section class="stats-grid stats-grid--invoice">
      <MetricCard
        v-for="item in statCards"
        :key="item.label"
        :label="item.label"
        :value="item.value"
        :prefix="item.prefix"
        :suffix="item.suffix"
        :trend="item.trend"
        :trend-label="item.trendLabel"
        :tone="item.tone"
        :icon="item.icon"
      />
    </section>

    <section class="page-panel surface-card">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">申请筛选</h3>
          <p class="panel-heading__desc">支持按申请单号、手机号、邮箱及状态快速定位记录。</p>
        </div>
      </div>

      <div class="filter-bar">
        <div class="filter-group">
          <el-input v-model="keyword" placeholder="搜索申请单号、手机号、邮箱" :prefix-icon="Search" clearable style="width: 280px" />
          <el-select v-model="statusFilter" placeholder="处理状态" style="width: 150px" clearable>
            <el-option label="待开票" value="0" />
            <el-option label="已开具" value="1" />
            <el-option label="已驳回" value="2" />
          </el-select>
          <el-button @click="resetFilters">重置</el-button>
        </div>

        <div class="filter-meta">当前匹配 {{ filteredRows.length }} 条</div>
      </div>
    </section>

    <section class="page-panel surface-card table-shell" v-loading="loading">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">开票申请列表</h3>
          <p class="panel-heading__desc">对待开票申请进行审核处理，支持直接进入开票动作。</p>
        </div>
      </div>

      <el-table v-if="pagedRows.length" :data="pagedRows" stripe border>
        <el-table-column prop="invoice_no" label="申请单号" width="180">
          <template #default="scope">
            <span class="font-mono">{{ scope.row.invoice_no }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="申请时间" width="170" />
        <el-table-column prop="user_phone" label="申请手机号" width="130" />
        <el-table-column prop="email" label="接收邮箱" min-width="200" />
        <el-table-column prop="amount" label="开票金额" width="120" align="right">
          <template #default="scope">
            <strong class="amount">¥{{ Number(scope.row.amount || 0).toFixed(2) }}</strong>
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
              v-if="Number(scope.row.status) === 0"
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

      <EmptyStateBlock
        v-else-if="!loading"
        title="暂无开票申请"
        description="当前筛选条件下没有记录，可尝试重置筛选。"
      />

      <div class="pager">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="filteredRows.length"
        />
      </div>
    </section>

    <el-dialog v-model="processDialogVisible" title="开具电子发票" width="560px">
      <div v-if="currentInvoice" class="invoice-summary mb-6">
        <div class="summary-item">
          <span>申请单号：</span><strong>{{ currentInvoice.invoice_no }}</strong>
        </div>
        <div class="summary-item">
          <span>接收邮箱：</span><strong>{{ currentInvoice.email }}</strong>
        </div>
        <div class="summary-item">
          <span>开票金额：</span><strong class="amount">¥{{ Number(currentInvoice.amount || 0).toFixed(2) }}</strong>
        </div>
      </div>

      <div class="upload-area" @click="simulateUpload" v-if="!uploadedFile && !isUploading">
        <el-icon class="upload-icon"><UploadFilled /></el-icon>
        <div class="upload-text">点击上传发票文件（PDF/JPG）</div>
      </div>

      <div v-if="isUploading" class="upload-progress">
        <span class="upload-tip">文件上传处理中...</span>
        <el-progress :percentage="uploadProgress" :stroke-width="10" striped striped-flow />
      </div>

      <div v-if="uploadedFile" class="upload-success">
        <el-icon color="#67C23A" :size="24" class="mr-2"><Check /></el-icon>
        <span>发票文件已就绪 (INV_auto_gen.pdf)</span>
        <el-button link type="danger" @click="uploadedFile = ''" style="margin-left: auto;">重新上传</el-button>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button type="danger" plain @click="submitProcess('reject')" :icon="Close">驳回申请</el-button>
          <div>
            <el-button @click="processDialogVisible = false">暂不处理</el-button>
            <el-button type="primary" @click="submitProcess('approve')" :disabled="!uploadedFile">确认开具并发送</el-button>
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.invoice-management-page {
  padding-bottom: 10px;
}

.stats-grid--invoice {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.filter-group {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.filter-meta {
  color: var(--color-text-2);
  font-size: 13px;
}

.font-mono {
  font-family: var(--font-family-mono);
}

.amount {
  color: #0f766e;
  font-weight: 700;
}

.pager {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
}

.mb-6 {
  margin-bottom: 24px;
}

.mr-2 {
  margin-right: 8px;
}

.invoice-summary {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 10px;
  border: 1px solid #ebeef5;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.summary-item:last-child {
  margin-bottom: 0;
}

.summary-item span {
  color: #909399;
}

.summary-item strong {
  color: #303133;
}

.upload-area {
  border: 2px dashed #dcdfe6;
  border-radius: 10px;
  padding: 32px 0;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background: #fafafa;
}

.upload-area:hover {
  border-color: #409eff;
  background: #ecf5ff;
}

.upload-icon {
  font-size: 46px;
  color: #c0c4cc;
  margin-bottom: 12px;
}

.upload-text {
  font-size: 14px;
  color: #606266;
}

.upload-progress {
  display: flex;
  flex-direction: column;
  padding: 20px 0;
}

.upload-tip {
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
}

.upload-success {
  display: flex;
  align-items: center;
  background: #f0f9eb;
  border: 1px solid #e1f3d8;
  padding: 16px;
  border-radius: 8px;
  color: #67c23a;
  font-weight: 500;
}

.dialog-footer {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

@media (max-width: 1280px) {
  .stats-grid--invoice {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .stats-grid--invoice {
    grid-template-columns: 1fr;
  }
}
</style>
