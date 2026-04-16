<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import { createDiscount, fetchDiscounts } from '../../api/operator'
import { mockDiscounts } from '../../mock/backoffice'

const loading = ref(false)
const rows = ref([])
const dialogVisible = ref(false)
const form = reactive({ name: '', campaign_type: '满减', discount_value: 8.8, threshold: 30, audience: 'fleet', status: 'draft' })

const loadData = async () => {
  loading.value = true
  try {
    const res = await fetchDiscounts()
    rows.value = res.data.data || mockDiscounts
  } catch (error) {
    rows.value = mockDiscounts
  } finally {
    loading.value = false
  }
}

const save = async () => {
  try {
    await createDiscount({ ...form })
  } catch (error) {
    rows.value.unshift({ ...form, id: Date.now(), redeem_count: 0, conversion_rate: '0%', status: '待审核' })
  }
  ElMessage.success('折扣活动已创建')
  dialogVisible.value = false
  loadData()
}

onMounted(loadData)
</script>

<template>
  <div class="page-shell">
    <PageSectionHeader eyebrow="营销管理" title="折扣优惠" description="承接运营商折扣活动的创建、审核与执行概览。" chip="活动管理">
      <template #actions>
        <el-button type="primary" @click="dialogVisible = true">新建活动</el-button>
      </template>
    </PageSectionHeader>

    <section class="page-panel surface-card table-shell">
      <el-table :data="rows" v-loading="loading">
        <el-table-column prop="name" label="活动名称" min-width="180" />
        <el-table-column prop="campaign_type" label="类型" width="100" />
        <el-table-column prop="discount_value" label="优惠值" width="120" />
        <el-table-column prop="threshold" label="门槛" width="120" />
        <el-table-column prop="audience" label="投放对象" width="120" />
        <el-table-column prop="redeem_count" label="核销量" width="100" />
        <el-table-column prop="conversion_rate" label="转化率" width="100" />
        <el-table-column prop="status" label="状态" width="120" />
      </el-table>
    </section>

    <el-dialog v-model="dialogVisible" title="新建折扣活动" width="520px">
      <div class="form-grid">
        <el-form-item label="活动名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="活动类型">
          <el-select v-model="form.campaign_type">
            <el-option label="满减" value="满减" />
            <el-option label="折扣" value="折扣" />
          </el-select>
        </el-form-item>
        <el-form-item label="优惠值"><el-input-number v-model="form.discount_value" :step="0.1" style="width: 100%" /></el-form-item>
        <el-form-item label="门槛"><el-input-number v-model="form.threshold" :step="10" style="width: 100%" /></el-form-item>
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
