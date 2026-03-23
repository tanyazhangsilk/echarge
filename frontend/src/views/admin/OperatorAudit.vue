<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { fetchOperatorAudits, processOperatorAudit } from '../../api/admin'

const loading = ref(false)
const list = ref([])
const summary = ref({ pending_count: 0, approved_count: 0, rejected_count: 0 })

const stats = computed(() => [
  { label: '待审核', value: summary.value.pending_count, meta: '优先处理准入阻塞项' },
  { label: '已通过', value: summary.value.approved_count, meta: '可继续站点接入与结算' },
  { label: '已驳回', value: summary.value.rejected_count, meta: '需要运营商补充材料' },
  { label: '总申请数', value: list.value.length, meta: '覆盖当前全部入驻主体' },
])

const loadData = async () => {
  loading.value = true
  try {
    const res = await fetchOperatorAudits()
    list.value = res.data.data || []
    summary.value = res.data.summary || summary.value
  } finally {
    loading.value = false
  }
}

const handleAction = async (row, action) => {
  const title = action === 'approve' ? '确认通过该运营商？' : '确认驳回该运营商？'
  const prompt = action === 'approve' ? '通过后将进入可运营状态。' : '驳回后会进入待补充材料状态。'
  const { value } = await ElMessageBox.prompt(prompt, title, {
    confirmButtonText: '确认',
    cancelButtonText: '取消',
    inputPlaceholder: '可选填写审核意见',
  }).catch(() => ({ value: null }))
  if (value === null) return
  await processOperatorAudit(row.id, { action, remark: value || '' })
  ElMessage.success(action === 'approve' ? '已通过审核' : '已驳回申请')
  loadData()
}
</script>

<template>
  <div class="page-shell">
    <section class="page-hero surface-card">
      <div>
        <p class="page-hero__eyebrow">Operator Admission</p>
        <h1 class="page-hero__title">运营商入驻审核</h1>
        <p class="page-hero__desc">承接平台管理员对入驻主体的资质复核、账户校验和准入决策，确保后续站点和财务动作都建立在合规主体上。</p>
      </div>
      <span class="micro-chip">管理员工作流</span>
    </section>

    <section class="stats-grid">
      <article v-for="item in stats" :key="item.label" class="stat-surface surface-card">
        <p class="stat-surface__label">{{ item.label }}</p>
        <h3 class="stat-surface__value">{{ item.value }}</h3>
        <p class="stat-surface__meta">{{ item.meta }}</p>
      </article>
    </section>

    <section class="page-panel surface-card table-shell">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">准入队列</h3>
          <p class="panel-heading__desc">用正式队列替换占位页，支持查看主体信息、审核意见和通过/驳回动作。</p>
        </div>
      </div>

      <el-table :data="list" v-loading="loading">
        <el-table-column prop="name" label="运营商" min-width="180" />
        <el-table-column prop="org_type" label="类型" width="120" />
        <el-table-column prop="contact_email" label="联系邮箱" min-width="180" />
        <el-table-column prop="contact_phone" label="联系电话" width="140" />
        <el-table-column prop="station_count" label="站点数" width="90" />
        <el-table-column prop="fleet_count" label="车队数" width="90" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.status === 'approved' ? 'success' : row.status === 'rejected' ? 'danger' : 'warning'">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="审核意见" min-width="200" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="handleAction(row, 'approve')">通过</el-button>
            <el-button size="small" plain type="danger" @click="handleAction(row, 'reject')">驳回</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>
