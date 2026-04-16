<script setup>
import { computed, onMounted, ref } from 'vue'

import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import { fetchCustomerOverview } from '../../api/operator'
import { mockCustomerOverview } from '../../mock/backoffice'

const loading = ref(false)
const members = ref([])
const summary = ref(mockCustomerOverview.summary)

const stats = computed(() => [
  { label: '车队数量', value: summary.value.fleet_count, meta: '已建立企业车队关系' },
  { label: '白名单车队', value: summary.value.whitelist_count, meta: '享受专属接入策略' },
  { label: '成员数量', value: summary.value.member_count, meta: '用于客户精细化运营' },
  { label: '重点成员', value: members.value.length, meta: '当前展示的重点客户样本' },
])

const loadData = async () => {
  loading.value = true
  try {
    const res = await fetchCustomerOverview()
    members.value = res.data.data.members || mockCustomerOverview.members
    summary.value = res.data.data.summary || mockCustomerOverview.summary
  } catch (error) {
    members.value = mockCustomerOverview.members
    summary.value = mockCustomerOverview.summary
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div class="page-shell">
    <PageSectionHeader eyebrow="客户管理" title="车队与白名单" description="在一个页面内查看车队成员、白名单归属与当前状态。" chip="客户总览" />

    <section class="stats-grid">
      <article v-for="item in stats" :key="item.label" class="stat-surface surface-card">
        <p class="stat-surface__label">{{ item.label }}</p>
        <h3 class="stat-surface__value">{{ item.value }}</h3>
        <p class="stat-surface__meta">{{ item.meta }}</p>
      </article>
    </section>

    <section class="page-panel surface-card table-shell">
      <el-table :data="members" v-loading="loading">
        <el-table-column prop="name" label="成员" min-width="180" />
        <el-table-column prop="phone" label="联系方式" width="160" />
        <el-table-column prop="fleet_name" label="所属车队" min-width="180" />
        <el-table-column prop="is_whitelist" label="白名单" width="100">
          <template #default="{ row }"><el-tag :type="row.is_whitelist ? 'success' : 'info'">{{ row.is_whitelist ? '是' : '否' }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120" />
      </el-table>
    </section>
  </div>
</template>
