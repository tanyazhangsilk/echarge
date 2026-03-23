<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { fetchSystemParams, updateSystemParams } from '../../api/admin'

const loading = ref(false)
const form = reactive({
  station_auto_publish: false,
  invoice_auto_approve_limit: 300,
  settlement_platform_rate: 10,
  abnormal_order_sla_minutes: 30,
  user_refund_limit_per_day: 2,
  support_email: '',
})

const loadData = async () => {
  loading.value = true
  try {
    const res = await fetchSystemParams()
    Object.assign(form, res.data.data || {})
  } finally {
    loading.value = false
  }
}

const save = async () => {
  loading.value = true
  try {
    await updateSystemParams({ ...form })
    ElMessage.success('系统参数已保存')
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
        <p class="page-hero__eyebrow">System Parameters</p>
        <h1 class="page-hero__title">系统参数设置</h1>
        <p class="page-hero__desc">将平台级规则从占位页升级为可维护的配置页，覆盖自动上架、发票自动审批、清分比例和异常订单 SLA 等关键规则。</p>
      </div>
      <span class="micro-chip">平台级参数</span>
    </section>

    <section class="page-panel surface-card">
      <div class="form-grid">
        <div class="soft-card" style="padding: 16px;">
          <div class="panel-heading">
            <div>
              <h3 class="panel-heading__title">自动化规则</h3>
              <p class="panel-heading__desc">影响平台审核和售后流转效率。</p>
            </div>
          </div>
          <el-form label-position="top">
            <el-form-item label="电站审核通过后自动上架">
              <el-switch v-model="form.station_auto_publish" />
            </el-form-item>
            <el-form-item label="发票自动审批阈值（元）">
              <el-input-number v-model="form.invoice_auto_approve_limit" :min="0" :step="50" style="width: 100%;" />
            </el-form-item>
            <el-form-item label="异常订单 SLA（分钟）">
              <el-input-number v-model="form.abnormal_order_sla_minutes" :min="5" :step="5" style="width: 100%;" />
            </el-form-item>
          </el-form>
        </div>

        <div class="soft-card" style="padding: 16px;">
          <div class="panel-heading">
            <div>
              <h3 class="panel-heading__title">财务与客服规则</h3>
              <p class="panel-heading__desc">影响资金结算节奏和客服兜底能力。</p>
            </div>
          </div>
          <el-form label-position="top">
            <el-form-item label="平台清分比例（%）">
              <el-input-number v-model="form.settlement_platform_rate" :min="1" :max="100" style="width: 100%;" />
            </el-form-item>
            <el-form-item label="用户每日退款上限">
              <el-input-number v-model="form.user_refund_limit_per_day" :min="1" style="width: 100%;" />
            </el-form-item>
            <el-form-item label="支持邮箱">
              <el-input v-model="form.support_email" />
            </el-form-item>
          </el-form>
        </div>
      </div>

      <div style="margin-top: 16px; display: flex; justify-content: flex-end;">
        <el-button type="primary" :loading="loading" @click="save">保存参数</el-button>
      </div>
    </section>
  </div>
</template>
