<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { fetchAdminUsers, toggleAdminUserBlacklist } from '../../api/admin'

const loading = ref(false)
const users = ref([])
const summary = ref({ total_users: 0, blacklisted_users: 0, active_users: 0 })

const stats = computed(() => [
  { label: '用户总数', value: summary.value.total_users, meta: '覆盖平台全部注册用户' },
  { label: '活跃用户', value: summary.value.active_users, meta: '可正常下单与支付' },
  { label: '黑名单用户', value: summary.value.blacklisted_users, meta: '用于风控拦截和人工恢复' },
  { label: '累计消费', value: `¥${users.value.reduce((sum, item) => sum + Number(item.total_spent || 0), 0).toFixed(0)}`, meta: '已沉淀的消费贡献' },
])

const loadData = async () => {
  loading.value = true
  try {
    const res = await fetchAdminUsers()
    users.value = res.data.data || []
    summary.value = res.data.summary || summary.value
  } finally {
    loading.value = false
  }
}

const toggleBlacklist = async (row) => {
  await toggleAdminUserBlacklist(row.id)
  ElMessage.success(row.status === 'blacklisted' ? '已移出黑名单' : '已加入黑名单')
  loadData()
}

onMounted(loadData)
</script>

<template>
  <div class="page-shell">
    <section class="page-hero surface-card">
      <div>
        <p class="page-hero__eyebrow">User Center</p>
        <h1 class="page-hero__title">平台用户管理</h1>
        <p class="page-hero__desc">管理用户状态、累计消费与黑名单动作，替代原本只显示占位说明的管理员用户页。</p>
      </div>
      <span class="micro-chip">风控与服务协同</span>
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
          <h3 class="panel-heading__title">用户列表</h3>
          <p class="panel-heading__desc">直接接入后台数据，可执行黑名单操作并查看用户消费与订单概况。</p>
        </div>
      </div>
      <el-table :data="users" v-loading="loading">
        <el-table-column prop="name" label="用户" min-width="160" />
        <el-table-column prop="phone" label="手机号" width="150" />
        <el-table-column prop="vin_code" label="VIN" min-width="180" />
        <el-table-column prop="order_count" label="订单数" width="100" />
        <el-table-column prop="total_spent" label="累计消费" width="120">
          <template #default="{ row }">¥{{ Number(row.total_spent || 0).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.status === 'blacklisted' ? 'danger' : 'success'">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="注册时间" width="180" />
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button size="small" :type="row.status === 'blacklisted' ? 'success' : 'danger'" plain @click="toggleBlacklist(row)">
              {{ row.status === 'blacklisted' ? '恢复' : '拉黑' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>
