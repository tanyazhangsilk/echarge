<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchCustomerOverview } from '../../api/operator'

const loading = ref(false)
const members = ref([])
const summary = ref({ fleet_count: 0, whitelist_count: 0, member_count: 0 })

const stats = computed(() => [
  { label: '车队数量', value: summary.value.fleet_count, meta: '已建立企业车队关系' },
  { label: '白名单车队', value: summary.value.whitelist_count, meta: '享受专属接入策略' },
  { label: '成员数量', value: summary.value.member_count, meta: '用于精细化客户运营' },
  { label: '黑名单成员', value: members.value.filter((item) => item.status === 'blacklisted').length, meta: '需要平台协同处理' },
])

const loadData = async () => {
  loading.value = true
  try {
    const res = await fetchCustomerOverview()
    members.value = res.data.data.members || []
    summary.value = res.data.data.summary || summary.value
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div class="page-shell">
    <section class="page-hero surface-card">
      <div>
        <p class="page-hero__eyebrow">Customer Hub</p>
        <h1 class="page-hero__title">车队与白名单</h1>
        <p class="page-hero__desc">在一个页面里查看车队成员、白名单归属和当前状态，用于运营商做客户经营与权益配置。</p>
      </div>
      <span class="micro-chip">客户资产总览</span>
    </section>

    <section class="stats-grid">
      <article v-for="item in stats" :key="item.label" class="stat-surface surface-card">
        <p class="stat-surface__label">{{ item.label }}</p>
        <h3 class="stat-surface__value">{{ item.value }}</h3>
        <p class="stat-surface__meta">{{ item.meta }}</p>
      </article>
    </section>

    <section class="page-panel surface-card table-shell">
      <el-table :data="members" v-loading="loading">
        <el-table-column prop="name" label="成员" min-width="160" />
        <el-table-column prop="phone" label="手机号" width="150" />
        <el-table-column prop="fleet_name" label="所属车队" min-width="180" />
        <el-table-column prop="is_whitelist" label="白名单" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_whitelist ? 'success' : 'info'">{{ row.is_whitelist ? '是' : '否' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120" />
      </el-table>
    </section>
  </div>
</template>
