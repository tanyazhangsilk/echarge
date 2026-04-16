<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import { createCoupon, dispatchCoupon, fetchCoupons } from '../../api/operator'
import { mockCoupons } from '../../mock/backoffice'

const loading = ref(false)
const rows = ref([])
const dialogVisible = ref(false)
const form = reactive({ name: '', campaign_type: '优惠券', discount_value: 10, threshold: 0, audience: 'all', status: 'active' })

const loadData = async () => {
  loading.value = true
  try {
    const res = await fetchCoupons()
    rows.value = res.data.data || mockCoupons
  } catch (error) {
    rows.value = mockCoupons
  } finally {
    loading.value = false
  }
}

const save = async () => {
  try {
    await createCoupon({ ...form })
  } catch (error) {
    rows.value.unshift({ id: Date.now(), name: form.name, discount_value: `${form.discount_value} 元`, inventory: 1000, dispatched: 0, used: 0, status: '待投放' })
  }
  ElMessage.success('优惠券活动已创建')
  dialogVisible.value = false
  loadData()
}

const dispatch = async (row) => {
  try {
    await dispatchCoupon(row.id, { dispatch_count: 100 })
  } catch (error) {
    row.dispatched = Number(row.dispatched || 0) + 100
  }
  ElMessage.success('已追加发放 100 张')
  loadData()
}

onMounted(loadData)
</script>

<template>
  <div class="page-shell">
    <PageSectionHeader eyebrow="营销管理" title="优惠券发放" description="支持创建券活动、跟踪库存并追加发放数量。" chip="券中心">
      <template #actions>
        <el-button type="primary" @click="dialogVisible = true">创建券活动</el-button>
      </template>
    </PageSectionHeader>

    <section class="page-panel surface-card table-shell">
      <el-table :data="rows" v-loading="loading">
        <el-table-column prop="name" label="活动名称" min-width="180" />
        <el-table-column prop="discount_value" label="面额" width="100" />
        <el-table-column prop="inventory" label="总库存" width="100" />
        <el-table-column prop="dispatched" label="已发放" width="100" />
        <el-table-column prop="used" label="已核销" width="100" />
        <el-table-column prop="status" label="状态" width="120" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }"><el-button size="small" type="primary" plain @click="dispatch(row)">追加发券</el-button></template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog v-model="dialogVisible" title="创建优惠券活动" width="480px">
      <el-form label-position="top">
        <el-form-item label="活动名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="券面金额"><el-input-number v-model="form.discount_value" :step="1" style="width: 100%" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
