<script setup>
import { onMounted, ref } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'

import { fetchMarketingAudits, processMarketingAudit } from '../../api/admin'

const loading = ref(false)
const rows = ref([])

const loadData = async () => {
  loading.value = true
  try {
    const res = await fetchMarketingAudits()
    rows.value = res.data.data || []
  } finally {
    loading.value = false
  }
}

const handleAudit = async (row, action) => {
  const { value } = await ElMessageBox.prompt('填写审核意见，可为空', action === 'approve' ? '通过活动' : '驳回活动', {
    inputPlaceholder: '审核意见',
  }).catch(() => ({ value: null }))
  if (value === null) return
  await processMarketingAudit(row.id, { action, remark: value || '' })
  ElMessage.success('审核结果已更新')
  loadData()
}

onMounted(loadData)
</script>

<template>
  <div class="page-shell">
    <section class="page-hero surface-card">
      <div>
        <p class="page-hero__eyebrow">Marketing Compliance</p>
        <h1 class="page-hero__title">营销合规审计</h1>
        <p class="page-hero__desc">用于平台审核运营商发起的折扣活动，确保优惠规则、投放对象与执行状态都在平台可控范围内。</p>
      </div>
      <span class="micro-chip">活动审计</span>
    </section>

    <section class="page-panel surface-card table-shell">
      <el-table :data="rows" v-loading="loading">
        <el-table-column prop="name" label="活动名称" min-width="180" />
        <el-table-column prop="operator_name" label="发起方" min-width="160" />
        <el-table-column prop="campaign_type" label="类型" width="100" />
        <el-table-column prop="discount_value" label="优惠值" width="100" />
        <el-table-column prop="audience" label="投放对象" width="120" />
        <el-table-column prop="audit_status" label="审核状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.audit_status === 'approved' ? 'success' : row.audit_status === 'rejected' ? 'danger' : 'warning'">
              {{ row.audit_status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="审核意见" min-width="200" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="handleAudit(row, 'approve')">通过</el-button>
            <el-button size="small" plain type="danger" @click="handleAudit(row, 'reject')">驳回</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>
