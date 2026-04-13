<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { RefreshRight } from '@element-plus/icons-vue'

import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
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
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.response?.data?.message || '系统参数加载失败')
  } finally {
    loading.value = false
  }
}

const save = async () => {
  loading.value = true
  try {
    await updateSystemParams({ ...form })
    ElMessage.success('系统参数已保存')
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.response?.data?.message || '系统参数保存失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div class="page-shell system-params-page">
    <PageSectionHeader
      eyebrow="系统配置"
      title="系统设置"
      description="维护平台参数、自动化规则与服务阈值。"
      chip="平台参数"
    >
      <template #actions>
        <el-button :icon="RefreshRight" :loading="loading" @click="loadData">刷新</el-button>
      </template>
    </PageSectionHeader>

    <section class="page-panel surface-card">
      <div class="form-grid">
        <div class="soft-card section-card">
          <div class="panel-heading">
            <div>
              <h3 class="panel-heading__title">审核与异常规则</h3>
              <p class="panel-heading__desc">配置审核流转和异常订单处理时限。</p>
            </div>
          </div>
          <el-form label-position="top">
            <el-form-item label="电站审核通过后自动公开">
              <el-switch v-model="form.station_auto_publish" />
            </el-form-item>
            <el-form-item label="发票自动审批阈值（元）">
              <el-input-number v-model="form.invoice_auto_approve_limit" :min="0" :step="50" style="width: 100%" />
            </el-form-item>
            <el-form-item label="异常订单处理时限（分钟）">
              <el-input-number v-model="form.abnormal_order_sla_minutes" :min="5" :step="5" style="width: 100%" />
            </el-form-item>
          </el-form>
        </div>

        <div class="soft-card section-card">
          <div class="panel-heading">
            <div>
              <h3 class="panel-heading__title">资金与客服规则</h3>
              <p class="panel-heading__desc">配置清分比例、退款限制和联系方式。</p>
            </div>
          </div>
          <el-form label-position="top">
            <el-form-item label="平台清分比例（%）">
              <el-input-number v-model="form.settlement_platform_rate" :min="1" :max="100" style="width: 100%" />
            </el-form-item>
            <el-form-item label="用户每日退款上限">
              <el-input-number v-model="form.user_refund_limit_per_day" :min="1" style="width: 100%" />
            </el-form-item>
            <el-form-item label="支持邮箱">
              <el-input v-model="form.support_email" />
            </el-form-item>
          </el-form>
        </div>
      </div>

      <div class="footer-actions">
        <el-button type="primary" :loading="loading" @click="save">保存参数</el-button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.system-params-page {
  padding-bottom: 8px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.section-card {
  padding: 16px;
}

.footer-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

@media (max-width: 960px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
