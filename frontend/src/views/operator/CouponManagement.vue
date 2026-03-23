<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createCoupon, dispatchCoupon, fetchCoupons } from '../../api/operator'

const loading = ref(false)
const rows = ref([])
const dialogVisible = ref(false)
const form = reactive({ name: '', campaign_type: '优惠券', discount_value: 10, threshold: 0, audience: 'all', status: 'active' })

const loadData = async () => {
  loading.value = true
  try {
    const res = await fetchCoupons()
    rows.value = res.data.data || []
  } finally {
    loading.value = false
  }
}

const save = async () => {
  await createCoupon({ ...form })
  ElMessage.success('优惠券活动已创建')
  dialogVisible.value = false
  loadData()
}

const dispatch = async (row) => {
  await dispatchCoupon(row.id, { dispatch_count: 100 })
  ElMessage.success('已追加发放 100 张')
  loadData()
}

onMounted(loadData)
</script>

<template>
  <div class="page-shell">
    <section class="page-hero surface-card">
      <div>
        <p class="page-hero__eyebrow">Coupon Center</p>
        <h1 class="page-hero__title">优惠券发放</h1>
        <p class="page-hero__desc">支持创建券活动、追踪库存和追加发放数量，形成完整的发券管理闭环。</p>
      </div>
      <el-button type="primary" @click="dialogVisible = true">创建券活动</el-button>
    </section>

    <section class="page-panel surface-card table-shell">
      <el-table :data="rows" v-loading="loading">
        <el-table-column prop="name" label="活动名称" min-width="180" />
        <el-table-column prop="discount_value" label="面额" width="100" />
        <el-table-column prop="inventory" label="总库存" width="100" />
        <el-table-column prop="dispatched" label="已发放" width="100" />
        <el-table-column prop="used" label="已核销" width="100" />
        <el-table-column prop="status" label="状态" width="120" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" plain @click="dispatch(row)">追加发券</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog v-model="dialogVisible" title="创建优惠券活动" width="480px">
      <el-form label-position="top">
        <el-form-item label="活动名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="券面金额">
          <el-input-number v-model="form.discount_value" :step="1" style="width: 100%;" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
