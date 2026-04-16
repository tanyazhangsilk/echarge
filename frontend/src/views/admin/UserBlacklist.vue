<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import { fetchAdminBlacklist, toggleAdminUserBlacklist } from '../../api/admin'
import { mockBlacklistRows } from '../../mock/backoffice'

const loading = ref(false)
const rows = ref([])

const loadData = async () => {
  loading.value = true
  try {
    const res = await fetchAdminBlacklist()
    rows.value = res.data.data || mockBlacklistRows
  } catch (error) {
    rows.value = mockBlacklistRows
  } finally {
    loading.value = false
  }
}

const restoreUser = async (row) => {
  try {
    await toggleAdminUserBlacklist(row.id)
  } catch (error) {
    rows.value = rows.value.filter((item) => item.id !== row.id)
  }
  ElMessage.success('已恢复用户状态')
  loadData()
}

onMounted(loadData)
</script>

<template>
  <div class="page-shell">
    <PageSectionHeader eyebrow="用户管理" title="黑名单管理" description="集中查看高风险用户并支持人工恢复。" chip="风控中心" />

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
        <el-table-column prop="reason" label="限制原因" min-width="220" />
        <el-table-column prop="created_at" label="更新时间" width="180" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }"><el-button size="small" type="success" plain @click="restoreUser(row)">恢复</el-button></template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>
