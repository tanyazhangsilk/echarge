<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createFleet, fetchFleets } from '../../api/operator'

const loading = ref(false)
const rows = ref([])
const dialogVisible = ref(false)
const form = reactive({ name: '', is_whitelist: false })

const loadData = async () => {
  loading.value = true
  try {
    const res = await fetchFleets()
    rows.value = res.data.data || []
  } finally {
    loading.value = false
  }
}

const save = async () => {
  await createFleet({ ...form })
  ElMessage.success('车队已创建')
  dialogVisible.value = false
  form.name = ''
  form.is_whitelist = false
  loadData()
}

onMounted(loadData)
</script>

<template>
  <div class="page-shell">
    <section class="page-hero surface-card">
      <div>
        <p class="page-hero__eyebrow">Fleet Management</p>
        <h1 class="page-hero__title">专属用户管理</h1>
        <p class="page-hero__desc">用于维护企业车队与白名单车队，把客户组织结构正式纳入运营商后台。</p>
      </div>
      <el-button type="primary" @click="dialogVisible = true">新建车队</el-button>
    </section>

    <section class="page-panel surface-card table-shell">
      <el-table :data="rows" v-loading="loading">
        <el-table-column prop="name" label="车队名称" min-width="180" />
        <el-table-column prop="member_count" label="成员数" width="100" />
        <el-table-column prop="is_whitelist" label="白名单" width="120">
          <template #default="{ row }">
            <el-tag :type="row.is_whitelist ? 'success' : 'info'">{{ row.is_whitelist ? '白名单' : '普通车队' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
      </el-table>
    </section>

    <el-dialog v-model="dialogVisible" title="新建车队" width="460px">
      <el-form label-position="top">
        <el-form-item label="车队名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="是否白名单">
          <el-switch v-model="form.is_whitelist" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
