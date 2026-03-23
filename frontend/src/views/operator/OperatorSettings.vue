<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchOperatorProfile, updateOperatorProfile } from '../../api/operator'

const loading = ref(false)
const form = reactive({
  name: '',
  org_type: '',
  contact_email: '',
  contact_phone: '',
  bank_account: '',
  verified: false,
  station_count: 0,
  fleet_count: 0,
})

const loadData = async () => {
  loading.value = true
  try {
    const res = await fetchOperatorProfile()
    Object.assign(form, res.data.data || {})
  } finally {
    loading.value = false
  }
}

const save = async () => {
  await updateOperatorProfile({
    name: form.name,
    org_type: form.org_type,
    contact_email: form.contact_email,
    contact_phone: form.contact_phone,
    bank_account: form.bank_account,
  })
  ElMessage.success('企业设置已保存')
}

onMounted(loadData)
</script>

<template>
  <div class="page-shell">
    <section class="page-hero surface-card">
      <div>
        <p class="page-hero__eyebrow">Operator Settings</p>
        <h1 class="page-hero__title">系统设置</h1>
        <p class="page-hero__desc">维护运营商主体资料、联系方式和收款账户，并展示当前主体的认证状态与资产概况。</p>
      </div>
      <span class="micro-chip">{{ form.verified ? '已认证' : '待认证' }}</span>
    </section>

    <section class="panel-grid panel-grid--wide">
      <article class="page-panel surface-card">
        <div class="panel-heading">
          <div>
            <h3 class="panel-heading__title">企业资料</h3>
            <p class="panel-heading__desc">保存后会同步更新运营商主体展示信息。</p>
          </div>
        </div>
        <div class="form-grid">
          <el-form-item label="企业名称">
            <el-input v-model="form.name" />
          </el-form-item>
          <el-form-item label="主体类型">
            <el-input v-model="form.org_type" />
          </el-form-item>
          <el-form-item label="联系邮箱">
            <el-input v-model="form.contact_email" />
          </el-form-item>
          <el-form-item label="联系电话">
            <el-input v-model="form.contact_phone" />
          </el-form-item>
          <el-form-item label="收款账户" style="grid-column: 1 / -1;">
            <el-input v-model="form.bank_account" />
          </el-form-item>
        </div>
        <div style="margin-top: 16px; display: flex; justify-content: flex-end;">
          <el-button type="primary" :loading="loading" @click="save">保存设置</el-button>
        </div>
      </article>

      <article class="page-panel surface-card">
        <div class="panel-heading">
          <div>
            <h3 class="panel-heading__title">当前概况</h3>
            <p class="panel-heading__desc">便于运营侧快速确认主体覆盖范围。</p>
          </div>
        </div>
        <div class="info-list">
          <div class="info-item">
            <p class="info-item__title">认证状态</p>
            <p class="info-item__desc">{{ form.verified ? '主体已通过平台认证，可继续扩展站点和营销功能。' : '主体仍处于待认证状态，请补全资质资料。' }}</p>
          </div>
          <div class="info-item">
            <p class="info-item__title">站点数量</p>
            <p class="info-item__desc">当前已纳入 {{ form.station_count }} 个站点资产。</p>
          </div>
          <div class="info-item">
            <p class="info-item__title">车队数量</p>
            <p class="info-item__desc">当前已建立 {{ form.fleet_count }} 个客户组织。</p>
          </div>
        </div>
      </article>
    </section>
  </div>
</template>
