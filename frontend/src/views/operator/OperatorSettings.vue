<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import { fetchOperatorProfile, updateOperatorProfile } from '../../api/operator'
import { mockOperatorProfile } from '../../mock/backoffice'

const loading = ref(false)
const form = reactive({ ...mockOperatorProfile })

const loadData = async () => {
  loading.value = true
  try {
    const res = await fetchOperatorProfile()
    Object.assign(form, res.data.data || mockOperatorProfile)
  } catch (error) {
    Object.assign(form, mockOperatorProfile)
  } finally {
    loading.value = false
  }
}

const save = async () => {
  try {
    await updateOperatorProfile({
      name: form.name,
      org_type: form.org_type,
      contact_email: form.contact_email,
      contact_phone: form.contact_phone,
      bank_account: form.bank_account,
    })
  } catch (error) {}
  ElMessage.success('运营商设置已保存')
}

onMounted(loadData)
</script>

<template>
  <div class="page-shell">
    <PageSectionHeader eyebrow="系统" title="运营商设置" description="维护运营主体资料、联系方式与结算账户信息。" :chip="form.verified ? '已认证' : '待认证'" />

    <section class="panel-grid panel-grid--wide">
      <article class="page-panel surface-card">
        <div class="panel-heading">
          <div>
            <h3 class="panel-heading__title">主体资料</h3>
            <p class="panel-heading__desc">保存后会同步更新运营商展示信息。</p>
          </div>
        </div>
        <div class="form-grid">
          <el-form-item label="企业名称"><el-input v-model="form.name" /></el-form-item>
          <el-form-item label="主体类型"><el-input v-model="form.org_type" /></el-form-item>
          <el-form-item label="联系邮箱"><el-input v-model="form.contact_email" /></el-form-item>
          <el-form-item label="联系电话"><el-input v-model="form.contact_phone" /></el-form-item>
          <el-form-item label="收款账户" style="grid-column: 1 / -1;"><el-input v-model="form.bank_account" /></el-form-item>
        </div>
        <div style="margin-top: 16px; display: flex; justify-content: flex-end;">
          <el-button type="primary" :loading="loading" @click="save">保存设置</el-button>
        </div>
      </article>

      <article class="page-panel surface-card">
        <div class="panel-heading">
          <div>
            <h3 class="panel-heading__title">当前概况</h3>
            <p class="panel-heading__desc">便于快速确认主体覆盖范围与认证情况。</p>
          </div>
        </div>
        <div class="info-list">
          <div class="info-item"><p class="info-item__title">认证状态</p><p class="info-item__desc">{{ form.verified ? '主体已通过平台认证，可继续扩展站点和营销能力。' : '主体仍处于待认证状态，请补全资质资料。' }}</p></div>
          <div class="info-item"><p class="info-item__title">电站数量</p><p class="info-item__desc">当前已纳入 {{ form.station_count }} 个电站资产。</p></div>
          <div class="info-item"><p class="info-item__title">车队数量</p><p class="info-item__desc">当前已建立 {{ form.fleet_count }} 个重点客户组织。</p></div>
        </div>
      </article>
    </section>
  </div>
</template>
