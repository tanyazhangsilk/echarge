<script setup>
import { computed, onActivated, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Close, Document, Download, RefreshRight, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import EmptyStateBlock from '../../components/console/EmptyStateBlock.vue'
import TableSkeletonBlock from '../../components/console/TableSkeletonBlock.vue'
import http from '../../api/http'
import { ROLES } from '../../config/permissions'
import { mockInvoiceRows } from '../../mock/backoffice'
import { readLocalListState, writeLocalListState } from '../../utils/localState'
import { buildRequestCacheKey, formatCacheLabel, getRequestCache, setRequestCache, shouldRefreshRequestCache } from '../../utils/requestCache'

const STORAGE_KEY = 'echarge-finance-invoices'
const CACHE_TTL = 60 * 1000

const route = useRoute()
const isAdmin = computed(() => route.meta?.role === ROLES.ADMIN)

const updateCacheLabel = (timestamp = Date.now()) => {
  cacheLabel.value = formatCacheLabel(timestamp)
}
const toNonEmptyRows = (items, fallback = []) => {
  if (Array.isArray(items) && items.length) return items
  if (Array.isArray(fallback) && fallback.length) return fallback
  return [...mockInvoiceRows]
}

const loading = ref(false)
const rows = ref(readLocalListState(STORAGE_KEY, mockInvoiceRows))
const keyword = ref('')
const activeStatus = ref('all')
const cacheLabel = ref('')
const tableReady = ref(rows.value.length > 0)

const currentPage = ref(1)
const pageSize = ref(10)

const processDialogVisible = ref(false)
const currentInvoice = ref(null)
const processRemark = ref('')
const uploadedFile = ref('')

const summary = reactive({
  pending_count: 0,
  issued_count: 0,
  rejected_count: 0,
  issued_amount: 0,
})

const cacheKey = buildRequestCacheKey('/finance/invoices', { scope: 'invoice-management' })

const statusFilteredRows = computed(() => {
  const baseRows = activeStatus.value === 'all' ? rows.value : rows.value.filter((item) => String(item.status) === activeStatus.value)
  const keywordText = keyword.value.trim().toLowerCase()
  if (!keywordText) return baseRows
  return baseRows.filter((item) =>
    [item.invoice_no, item.user_phone, item.email, item.invoice_title].filter(Boolean).some((field) => String(field).toLowerCase().includes(keywordText)),
  )
})

const pagedRows = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return statusFilteredRows.value.slice(start, start + pageSize.value)
})

const tabOptions = computed(() => [
  { key: 'all', label: '全部', count: rows.value.length },
  { key: '0', label: '待开票', count: summary.pending_count },
  { key: '1', label: '已开票', count: summary.issued_count },
  { key: '2', label: '已驳回', count: summary.rejected_count },
])

const stats = computed(() => [
  { label: '待开票', value: summary.pending_count, suffix: ' 笔', trend: '待处理池', trendLabel: '优先处理超时申请', tone: 'warning', icon: Document },
  { label: '已开票', value: summary.issued_count, suffix: ' 笔', trend: '已完成开票', trendLabel: '已触发邮件通知', tone: 'success', icon: Download },
  { label: '已驳回', value: summary.rejected_count, suffix: ' 笔', trend: '待补资料', trendLabel: '需记录驳回原因', tone: 'danger', icon: Close },
  {
    label: '已开票金额',
    value: Number(summary.issued_amount || 0).toFixed(2),
    prefix: '￥',
    trend: '财务统计口径',
    trendLabel: isAdmin.value ? '全平台汇总' : '当前运营商汇总',
    tone: 'primary',
    icon: RefreshRight,
  },
])

const getStatusType = (status) => (Number(status) === 0 ? 'warning' : Number(status) === 1 ? 'success' : 'danger')
const getStatusText = (row) => row?.status_text || (Number(row?.status) === 0 ? '待开票' : Number(row?.status) === 1 ? '已开票' : '已驳回')

const refreshSummary = () => {
  summary.pending_count = rows.value.filter((item) => Number(item.status) === 0).length
  summary.issued_count = rows.value.filter((item) => Number(item.status) === 1).length
  summary.rejected_count = rows.value.filter((item) => Number(item.status) === 2).length
  summary.issued_amount = rows.value
    .filter((item) => Number(item.status) === 1)
    .reduce((sum, item) => sum + Number(item.amount || 0), 0)
}

refreshSummary()

const applyRows = (items = [], { updatedAt = Date.now(), persist = true } = {}) => {
  const nextRows = toNonEmptyRows(items, rows.value)
  rows.value = nextRows
  if (persist && nextRows.length) {
    writeLocalListState(STORAGE_KEY, nextRows)
  }
  refreshSummary()
  currentPage.value = 1
  tableReady.value = true
  updateCacheLabel(updatedAt)
}

const fetchInvoices = async ({ background = false } = {}) => {
  const cached = getRequestCache(cacheKey, { ttl: CACHE_TTL, allowStale: true })
  if (cached) {
    applyRows(cached.value, { updatedAt: cached.updatedAt, persist: false })
  }

  loading.value = !cached || !background
  try {
    const res = await http.get('/finance/invoices', {
      params: {
        keyword: keyword.value.trim() || undefined,
      },
    })
    const remoteItems = Array.isArray(res?.data?.data) ? res.data.data : []
    const nextRows = toNonEmptyRows(remoteItems, rows.value)
    applyRows(nextRows, { updatedAt: Date.now(), persist: nextRows.length > 0 })
    if (nextRows.length) {
      setRequestCache(cacheKey, nextRows)
    }
  } catch (error) {
    const localRows = readLocalListState(STORAGE_KEY, mockInvoiceRows)
    const fallbackRows = toNonEmptyRows(localRows, rows.value)
    applyRows(fallbackRows, { updatedAt: Date.now(), persist: fallbackRows.length > 0 })
  } finally {
    loading.value = false
  }
}

const openProcessDialog = (row) => {
  currentInvoice.value = row
  processRemark.value = ''
  uploadedFile.value = row.file_url || ''
  processDialogVisible.value = true
}

const submitProcess = async (action) => {
  if (!currentInvoice.value) return
  if (action === 'approve' && !uploadedFile.value) {
    uploadedFile.value = `https://echarge-system.com/invoices/${currentInvoice.value.invoice_no}.pdf`
  }
  if (action === 'reject' && !processRemark.value.trim()) {
    ElMessage.warning('驳回时请填写备注说明')
    return
  }

  try {
    await ElMessageBox.confirm(action === 'approve' ? '确认开具发票并发送邮件通知？' : '确认驳回该申请并发送通知？', '操作确认', {
      type: action === 'approve' ? 'success' : 'warning',
    })
  } catch (error) {
    return
  }

  let remoteSuccess = false
  try {
    await http.post(`/finance/invoices/${currentInvoice.value.id}/process`, {
      action,
      file_url: uploadedFile.value,
      remark: processRemark.value,
    })
    remoteSuccess = true
  } catch (error) {
    remoteSuccess = false
  }

  rows.value = rows.value.map((item) =>
    item.id === currentInvoice.value.id
      ? {
          ...item,
          status: action === 'approve' ? 1 : 2,
          status_text: action === 'approve' ? '已开票' : '已驳回',
          file_url: uploadedFile.value,
          remark: processRemark.value || (action === 'approve' ? '已完成开票' : '资料需补充'),
        }
      : item,
  )
  writeLocalListState(STORAGE_KEY, rows.value)
  setRequestCache(cacheKey, rows.value)
  refreshSummary()
  updateCacheLabel(Date.now())
  processDialogVisible.value = false
  ElMessage.success(remoteSuccess ? (action === 'approve' ? '发票已处理为已开票' : '发票申请已驳回') : '发票状态已更新')
}

watch(activeStatus, () => {
  currentPage.value = 1
})

onMounted(() => fetchInvoices({ background: true }))
onActivated(() => {
  if (shouldRefreshRequestCache(cacheKey, CACHE_TTL)) {
    fetchInvoices({ background: true })
  }
})
</script>

<template>
  <div class="page-shell invoice-management-page">
    <PageSectionHeader
      eyebrow="财务管理"
      :title="isAdmin ? '平台发票管理' : '运营商发票管理'"
      :description="isAdmin ? '管理员可查看全平台发票记录并抽查详情。' : '运营商可处理待开票申请并上传发票文件。'"
      :chip="isAdmin ? '管理员视角' : '运营商视角'"
    >
      <template #actions>
        <el-tag v-if="cacheLabel" type="info" effect="plain">{{ cacheLabel }}</el-tag>
        <el-button :icon="RefreshRight" :loading="loading" @click="fetchInvoices()">刷新</el-button>
      </template>
    </PageSectionHeader>

    <section class="stats-grid stats-grid--invoice">
      <MetricCard v-for="item in stats" :key="item.label" v-bind="item" />
    </section>

    <section class="page-panel surface-card">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">筛选与状态切换</h3>
          <p class="panel-heading__desc">支持按状态、关键词筛选发票申请记录。</p>
        </div>
      </div>

      <div class="filter-bar">
        <el-input v-model="keyword" placeholder="搜索用户手机号、邮箱或发票抬头" :prefix-icon="Search" clearable style="width: 320px" />
        <el-button type="primary" :icon="Search" @click="fetchInvoices()">查询</el-button>
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

    <section class="page-panel surface-card table-shell">
      <TableSkeletonBlock v-if="loading && !tableReady" :rows="6" :columns="8" />

      <el-table v-else-if="pagedRows.length" :data="pagedRows" v-loading="loading" stripe>
        <el-table-column prop="invoice_no" label="申请单号" min-width="180" />
        <el-table-column prop="user_phone" label="用户手机号" width="140" />
        <el-table-column prop="invoice_title" label="发票抬头" min-width="200" />
        <el-table-column label="金额" width="110" align="right">
          <template #default="{ row }">￥{{ Number(row.amount || 0).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="110" align="center">
          <template #default="{ row }"><el-tag :type="getStatusType(row.status)">{{ getStatusText(row) }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="email" label="接收邮箱" min-width="180" />
        <el-table-column prop="created_at" label="申请时间" width="170" />
        <el-table-column prop="remark" label="处理备注" min-width="180" />
        <el-table-column v-if="!isAdmin" label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button v-if="Number(row.status) === 0" size="small" type="primary" @click="openProcessDialog(row)">处理</el-button>
            <span v-else class="text-muted">已处理</span>
          </template>
        </el-table-column>
      </el-table>

      <EmptyStateBlock v-else-if="!loading" title="暂无发票记录" description="当前筛选条件下没有匹配发票记录。" />

      <div class="pager">
        <el-pagination
          :current-page="currentPage"
          :page-size="pageSize"
          :page-sizes="[10, 20, 40]"
          :total="statusFilteredRows.length"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="(page) => { currentPage = page }"
          @size-change="(size) => { currentPage = 1; pageSize = size }"
        />
      </div>
    </section>

    <el-dialog v-model="processDialogVisible" title="处理发票申请" width="560px">
      <el-form label-width="96px">
        <el-form-item label="申请单号">
          <div>{{ currentInvoice?.invoice_no || '-' }}</div>
        </el-form-item>
        <el-form-item label="发票文件">
          <el-input v-model="uploadedFile" placeholder="可填写发票 PDF 链接；为空时会自动生成演示文件地址" />
        </el-form-item>
        <el-form-item label="处理备注">
          <el-input v-model="processRemark" type="textarea" :rows="4" placeholder="可填写开票说明或驳回原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="processDialogVisible = false">取消</el-button>
        <el-button plain type="danger" @click="submitProcess('reject')">驳回</el-button>
        <el-button type="primary" @click="submitProcess('approve')">确认开票</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.stats-grid--invoice {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.status-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 16px;
}

.status-tab {
  min-width: 120px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 14px;
  padding: 12px 16px;
  background: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  color: var(--color-text-1);
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.status-tab strong {
  font-size: 16px;
}

.status-tab:hover {
  border-color: rgba(64, 158, 255, 0.35);
  transform: translateY(-1px);
}

.status-tab--active {
  border-color: rgba(64, 158, 255, 0.7);
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.08), rgba(34, 197, 94, 0.08));
  box-shadow: 0 12px 24px -20px rgba(64, 158, 255, 0.7);
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
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

  .status-tab {
    width: 100%;
  }
}
</style>
