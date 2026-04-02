<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  Search,
  UploadFilled,
  Document,
  Check,
  Close,
  Message,
  Download,
  RefreshRight,
  View,
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import EmptyStateBlock from '../../components/console/EmptyStateBlock.vue'
import http from '../../api/http'
import { ROLES } from '../../config/permissions'

const route = useRoute()
const isAdmin = computed(() => route.meta?.role === ROLES.ADMIN)

const loading = ref(false)
const rows = ref([])
const keyword = ref('')
const activeStatus = ref('all')

const currentPage = ref(1)
const pageSize = ref(10)

const processDialogVisible = ref(false)
const detailVisible = ref(false)
const detailLoading = ref(false)
const currentInvoice = ref(null)
const detailData = ref(null)

const uploadProgress = ref(0)
const isUploading = ref(false)
const uploadedFile = ref('')
const processRemark = ref('')

const summary = reactive({
  pending_count: 0,
  issued_count: 0,
  rejected_count: 0,
  issued_amount: 0,
})

const statusFilteredRows = computed(() => {
  if (activeStatus.value === 'all') return rows.value
  return rows.value.filter((item) => String(item.status) === activeStatus.value)
})

const pagedRows = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return statusFilteredRows.value.slice(start, start + pageSize.value)
})

const tabOptions = computed(() => [
  { key: 'all', label: '全部', count: rows.value.length, tone: 'info' },
  { key: '0', label: '待开票', count: summary.pending_count, tone: 'warning' },
  { key: '1', label: '已开票', count: summary.issued_count, tone: 'success' },
  { key: '2', label: '已驳回', count: summary.rejected_count, tone: 'danger' },
])

const stats = computed(() => [
  {
    label: '待开票',
    value: summary.pending_count,
    suffix: ' 笔',
    trend: '待处理池',
    trendLabel: '优先处理超时申请',
    tone: 'warning',
    icon: Document,
  },
  {
    label: '已开票',
    value: summary.issued_count,
    suffix: ' 笔',
    trend: '已完成开票',
    trendLabel: '已触发邮件通知',
    tone: 'success',
    icon: Message,
  },
  {
    label: '已驳回',
    value: summary.rejected_count,
    suffix: ' 笔',
    trend: '待补资料',
    trendLabel: '需记录驳回原因',
    tone: 'danger',
    icon: Close,
  },
  {
    label: '已开票金额',
    value: Number(summary.issued_amount || 0).toFixed(2),
    prefix: '¥',
    trend: '财务统计口径',
    trendLabel: isAdmin.value ? '全平台汇总' : '当前运营商汇总',
    tone: 'primary',
    icon: Download,
  },
])

const getStatusType = (status) => {
  if (Number(status) === 0) return 'warning'
  if (Number(status) === 1) return 'success'
  return 'danger'
}

const getStatusText = (row) => row?.status_text || (Number(row?.status) === 0 ? '待开票' : Number(row?.status) === 1 ? '已开票' : '已驳回')

const fetchInvoices = async () => {
  loading.value = true
  try {
    const keywordParam = keyword.value.trim() || undefined
    const res = await http.get('/finance/invoices', {
      params: {
        keyword: keywordParam,
      },
    })

    if (res?.data?.code === 200) {
      rows.value = Array.isArray(res.data.data) ? res.data.data : []
      const s = res.data.summary || {}
      summary.pending_count = Number(s.pending_count || 0)
      summary.issued_count = Number(s.issued_count || 0)
      summary.rejected_count = Number(s.rejected_count || 0)
      summary.issued_amount = Number(s.issued_amount || 0)
      currentPage.value = 1
      return
    }
    ElMessage.error(res?.data?.message || '加载发票数据失败')
  } catch (error) {
    ElMessage.error('加载发票数据失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const openDetail = async (row) => {
  detailVisible.value = true
  detailLoading.value = true
  detailData.value = null
  try {
    const res = await http.get(`/finance/invoices/${row.id}`)
    if (res?.data?.code === 200) {
      detailData.value = res.data.data
      return
    }
    ElMessage.error(res?.data?.message || '加载发票详情失败')
  } catch (error) {
    ElMessage.error('加载发票详情失败')
  } finally {
    detailLoading.value = false
  }
}

const openProcessDialog = (row) => {
  currentInvoice.value = row
  processRemark.value = ''
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
        uploadedFile.value = `https://echarge-system.com/invoices/${currentInvoice.value?.invoice_no || 'invoice'}.pdf`
        ElMessage.success('发票文件上传成功')
      }, 400)
    }
  }, 160)
}

const submitProcess = async (action) => {
  if (!currentInvoice.value) return

  if (action === 'approve' && !uploadedFile.value) {
    ElMessage.warning('请先上传发票文件')
    return
  }
  if (action === 'reject' && !processRemark.value.trim()) {
    ElMessage.warning('驳回时请填写备注说明')
    return
  }

  const confirmText = action === 'approve' ? '确认开具发票并发送邮件通知？' : '确认驳回该申请并发送通知？'

  try {
    await ElMessageBox.confirm(confirmText, '操作确认', { type: action === 'approve' ? 'success' : 'warning' })
    const res = await http.post(`/finance/invoices/${currentInvoice.value.id}/process`, {
      action,
      file_url: uploadedFile.value,
      remark: processRemark.value,
    })

    if (res?.data?.code === 200) {
      ElMessage.success(res.data.message || '处理成功')
      processDialogVisible.value = false
      await fetchInvoices()
      return
    }
    ElMessage.error(res?.data?.message || '处理失败')
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('处理失败，请稍后重试')
    }
  }
}

const exportRows = () => {
  if (!statusFilteredRows.value.length) {
    ElMessage.warning('当前无可导出数据')
    return
  }

  const headers = ['申请单号', '用户手机号', '运营商', '金额', '状态', '申请时间', '处理备注']
  const lines = [headers.join(',')]
  statusFilteredRows.value.forEach((item) => {
    const row = [
      item.invoice_no,
      item.user_phone,
      item.operator_name || '',
      Number(item.amount || 0).toFixed(2),
      getStatusText(item),
      item.created_at,
      item.remark || '',
    ]
    lines.push(row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(','))
  })

  const csvContent = `\uFEFF${lines.join('\n')}`
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `发票记录_${new Date().toISOString().slice(0, 10)}.csv`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}

watch(activeStatus, () => {
  currentPage.value = 1
})

onMounted(fetchInvoices)
</script>

<template>
  <div class="page-shell invoice-management-page">
    <PageSectionHeader
      eyebrow="Invoice Management"
      :title="isAdmin ? '全平台发票管理' : '运营商发票管理'"
      :description="isAdmin ? '管理员可查看全平台发票记录并抽查详情。' : '运营商可处理待开票申请并上传发票文件。'"
      :chip="isAdmin ? '管理员视角（只读抽查）' : '运营商视角（可处理）'"
    >
      <template #actions>
        <el-button :icon="RefreshRight" :loading="loading" @click="fetchInvoices">刷新</el-button>
        <el-button type="primary" :icon="Download" @click="exportRows">导出记录</el-button>
      </template>
    </PageSectionHeader>

    <section class="stats-grid stats-grid--invoice">
      <MetricCard
        v-for="item in stats"
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
          <h3 class="panel-heading__title">筛选与状态切换</h3>
          <p class="panel-heading__desc">支持按状态、关键词筛选发票申请记录。</p>
        </div>
      </div>

      <div class="filter-bar">
        <el-input v-model="keyword" placeholder="搜索用户手机号、邮箱或发票抬头" :prefix-icon="Search" clearable style="width: 320px" @keyup.enter="fetchInvoices" />
        <el-button type="primary" :icon="Search" @click="fetchInvoices">查询</el-button>
      </div>

      <div class="status-tabs">
        <button
          v-for="item in tabOptions"
          :key="item.key"
          type="button"
          class="status-tab"
          :class="{ 'status-tab--active': activeStatus === item.key }"
          @click="activeStatus = item.key"
        >
          <span>{{ item.label }}</span>
          <strong>{{ item.count }}</strong>
        </button>
      </div>
    </section>

    <section class="page-panel surface-card table-shell" v-loading="loading">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">发票申请列表</h3>
          <p class="panel-heading__desc">当前共 {{ rows.length }} 条记录。</p>
        </div>
      </div>

      <el-table v-if="pagedRows.length" :data="pagedRows" stripe border>
        <el-table-column prop="invoice_no" label="申请单号" width="180" />
        <el-table-column prop="created_at" label="申请时间" width="170" />
        <el-table-column prop="user_phone" label="用户手机号" width="130" />
        <el-table-column v-if="isAdmin" prop="operator_name" label="运营商" min-width="160" />
        <el-table-column prop="email" label="接收邮箱" min-width="180" />
        <el-table-column prop="amount" label="开票金额" width="120" align="right">
          <template #default="{ row }">
            <strong class="amount">¥{{ Number(row.amount || 0).toFixed(2) }}</strong>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusText(row) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="160" show-overflow-tooltip />
        <el-table-column label="操作" width="170" fixed="right" align="center">
          <template #default="{ row }">
            <el-button link type="primary" :icon="View" @click="openDetail(row)">查看详情</el-button>
            <el-button
              v-if="!isAdmin && row.can_process"
              link
              type="success"
              @click="openProcessDialog(row)"
            >
              处理
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <EmptyStateBlock
        v-else-if="!loading"
        title="暂无发票记录"
        description="当前筛选条件下无数据，可调整状态或关键词重试。"
      />

      <div class="pager">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="statusFilteredRows.length"
        />
      </div>
    </section>

    <el-dialog v-model="processDialogVisible" title="处理发票申请" width="560px">
      <div v-if="currentInvoice" class="invoice-summary">
        <div class="summary-item"><span>申请单号：</span><strong>{{ currentInvoice.invoice_no }}</strong></div>
        <div class="summary-item"><span>接收邮箱：</span><strong>{{ currentInvoice.email }}</strong></div>
        <div class="summary-item"><span>开票金额：</span><strong class="amount">¥{{ Number(currentInvoice.amount || 0).toFixed(2) }}</strong></div>
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
        <el-icon color="#67C23A" :size="24"><Check /></el-icon>
        <span>发票文件已就绪</span>
        <el-button link type="danger" @click="uploadedFile = ''">重新上传</el-button>
      </div>

      <el-form label-width="88px" class="remark-form">
        <el-form-item label="处理备注">
          <el-input v-model="processRemark" type="textarea" :rows="3" placeholder="开票说明或驳回原因（驳回时必填）" />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button type="danger" plain @click="submitProcess('reject')" :icon="Close">驳回申请</el-button>
          <div>
            <el-button @click="processDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="submitProcess('approve')">确认开票并通知</el-button>
          </div>
        </div>
      </template>
    </el-dialog>

    <el-drawer v-model="detailVisible" title="发票申请详情" size="520px">
      <div v-loading="detailLoading">
        <el-descriptions v-if="detailData" :column="1" border>
          <el-descriptions-item label="申请单号">{{ detailData.invoice_no }}</el-descriptions-item>
          <el-descriptions-item label="用户手机号">{{ detailData.user_phone }}</el-descriptions-item>
          <el-descriptions-item label="运营商">{{ detailData.operator_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="订单号">{{ detailData.order_no || '-' }}</el-descriptions-item>
          <el-descriptions-item label="发票抬头">{{ detailData.invoice_title || '-' }}</el-descriptions-item>
          <el-descriptions-item label="金额">¥{{ Number(detailData.amount || 0).toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ detailData.email }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(detailData.status)">{{ getStatusText(detailData) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="发票文件">
            <el-link v-if="detailData.file_url" :href="detailData.file_url" target="_blank" type="primary">查看文件</el-link>
            <span v-else>未上传</span>
          </el-descriptions-item>
          <el-descriptions-item label="备注">{{ detailData.remark || '-' }}</el-descriptions-item>
          <el-descriptions-item label="申请时间">{{ detailData.created_at }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ detailData.updated_at }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-drawer>
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
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.status-tabs {
  margin-top: 14px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.status-tab {
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.9);
  padding: 10px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  transition: all 0.2s ease;
}

.status-tab span {
  color: var(--color-text-2);
  font-size: 13px;
}

.status-tab strong {
  color: var(--color-text);
}

.status-tab--active {
  border-color: rgba(47, 116, 255, 0.3);
  box-shadow: 0 12px 24px rgba(47, 116, 255, 0.12);
  transform: translateY(-1px);
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

.invoice-summary {
  background: #f8f9fa;
  padding: 14px;
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

.upload-area {
  margin-top: 12px;
  border: 2px dashed #dcdfe6;
  border-radius: 10px;
  padding: 28px 0;
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
  font-size: 42px;
  color: #c0c4cc;
  margin-bottom: 10px;
}

.upload-text {
  font-size: 14px;
  color: #606266;
}

.upload-progress {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.upload-tip {
  font-size: 13px;
  color: #606266;
}

.upload-success {
  margin-top: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  background: #f0f9eb;
  border: 1px solid #e1f3d8;
  padding: 12px;
  border-radius: 8px;
  color: #67c23a;
}

.remark-form {
  margin-top: 14px;
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

  .status-tabs {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .stats-grid--invoice,
  .status-tabs {
    grid-template-columns: 1fr;
  }
}
</style>
