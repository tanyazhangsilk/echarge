<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createBillingTemplate, fetchBillingTemplates, updateBillingTemplate } from '../../api/operator'

const loading = ref(false)
const rows = ref([])
const dialogVisible = ref(false)
const editingId = ref(null)
const form = reactive({
  name: '',
  peak_price: 1.88,
  flat_price: 1.32,
  valley_price: 0.68,
  service_price: 0.8,
  scope: 'all',
  status: 'active',
})

const resetForm = () => {
  editingId.value = null
  Object.assign(form, { name: '', peak_price: 1.88, flat_price: 1.32, valley_price: 0.68, service_price: 0.8, scope: 'all', status: 'active' })
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await fetchBillingTemplates()
    rows.value = res.data.data || []
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  resetForm()
  dialogVisible.value = true
}

const openEdit = (row) => {
  editingId.value = row.id
  Object.assign(form, row)
  dialogVisible.value = true
}

const save = async () => {
  if (editingId.value) {
    await updateBillingTemplate(editingId.value, { ...form })
    ElMessage.success('模板已更新')
  } else {
    await createBillingTemplate({ ...form })
    ElMessage.success('模板已创建')
  }
  dialogVisible.value = false
  loadData()
}

onMounted(loadData)
</script>

<template>
  <div class="page-shell">
    <section class="page-hero surface-card">
      <div>
        <p class="page-hero__eyebrow">Billing Templates</p>
        <h1 class="page-hero__title">计费模板管理</h1>
        <p class="page-hero__desc">统一管理尖峰平谷电价模板、服务费和作用范围，后续可继续扩展模板下发到站点的能力。</p>
      </div>
      <el-button type="primary" @click="openCreate">新建模板</el-button>
    </section>

    <section class="page-panel surface-card table-shell">
      <el-table :data="rows" v-loading="loading">
        <el-table-column prop="name" label="模板名称" min-width="180" />
        <el-table-column prop="peak_price" label="尖峰" width="100" />
        <el-table-column prop="flat_price" label="平段" width="100" />
        <el-table-column prop="valley_price" label="谷段" width="100" />
        <el-table-column prop="service_price" label="服务费" width="100" />
        <el-table-column prop="scope" label="作用范围" width="120" />
        <el-table-column prop="status" label="状态" width="120" />
        <el-table-column prop="updated_at" label="更新时间" width="180" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" plain @click="openEdit(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑模板' : '新建模板'" width="560px">
      <div class="form-grid">
        <el-form-item label="模板名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="作用范围">
          <el-select v-model="form.scope">
            <el-option label="全站" value="all" />
            <el-option label="指定站点" value="station" />
          </el-select>
        </el-form-item>
        <el-form-item label="尖峰电价">
          <el-input-number v-model="form.peak_price" :step="0.01" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="平段电价">
          <el-input-number v-model="form.flat_price" :step="0.01" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="谷段电价">
          <el-input-number v-model="form.valley_price" :step="0.01" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="服务费">
          <el-input-number v-model="form.service_price" :step="0.01" style="width: 100%;" />
        </el-form-item>
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
