<script setup>
import { onMounted, ref } from 'vue'
import { fetchAdminBlacklist, toggleAdminUserBlacklist } from '../../api/admin'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const rows = ref([])

const loadData = async () => {
  loading.value = true
  try {
    const res = await fetchAdminBlacklist()
    rows.value = res.data.data || []
  } finally {
    loading.value = false
  }
}

const restoreUser = async (row) => {
  await toggleAdminUserBlacklist(row.id)
  ElMessage.success('已恢复用户状态')
  loadData()
}

onMounted(loadData)
</script>

<template>
  <div class="page-shell">
    <section class="page-hero surface-card">
      <div>
        <p class="page-hero__eyebrow">Blacklist</p>
        <h1 class="page-hero__title">封禁用户管理</h1>
        <p class="page-hero__desc">集中查看已被风控拦截的用户，并支持管理员在复核后直接恢复账号状态。</p>
      </div>
      <span class="micro-chip">账号恢复中心</span>
    </section>

    <section class="page-panel surface-card table-shell">
      <div class="panel-heading">
        <div>
          <h3 class="panel-heading__title">黑名单列表</h3>
          <p class="panel-heading__desc">用于承接恢复审批与申诉处理流程。</p>
        </div>
      </div>
      <el-table :data="rows" v-loading="loading">
        <el-table-column prop="name" label="用户" min-width="160" />
        <el-table-column prop="phone" label="手机号" width="150" />
        <el-table-column prop="reason" label="封禁原因" min-width="180" />
        <el-table-column prop="created_at" label="更新时间" width="180" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="success" plain @click="restoreUser(row)">恢复</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>
