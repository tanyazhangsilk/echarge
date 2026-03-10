<script setup>
import { reactive, ref } from 'vue'
import { Upload, Check, InfoFilled } from '@element-plus/icons-vue'

// 模拟状态: 'unbound' (未绑定), 'pending' (审核中), 'verified' (已认证)
const verifyStatus = ref('unbound') 

const form = reactive({
  companyName: '',
  orgType: 'enterprise',
  bankAccount: '',
  bankName: ''
})

const submitForm = () => {
  console.log('提交绑卡资料', form)
  verifyStatus.value = 'pending'
}
</script>

<template>
  <div class="page-container flex flex-col gap-4">
    <el-card shadow="never" class="base-card">
      <template #header>
        <div class="card-header font-bold text-lg">
          <span>运营商资质与对公账户绑定</span>
        </div>
      </template>

      <el-alert v-if="verifyStatus === 'unbound'" title="您尚未绑定对公账户，暂不能开启 T+1 资金清分，请尽快完善资料。" type="warning" show-icon :closable="false" class="mb-6" />
      <el-alert v-else-if="verifyStatus === 'pending'" title="资料审核中，平台预计在 1-2 个工作日内完成处理。" type="info" show-icon :closable="false" class="mb-6" />
      <el-alert v-else title="认证已通过，T+1 清分服务已激活。" type="success" show-icon :closable="false" class="mb-6" />

      <el-form :model="form" label-width="120px" class="max-w-2xl" :disabled="verifyStatus !== 'unbound'">
        <el-form-item label="主体类型">
          <el-radio-group v-model="form.orgType">
            <el-radio label="enterprise" value="enterprise">企业</el-radio>
            <el-radio label="individual" value="individual">个体工商户</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="企业全称">
          <el-input v-model="form.companyName" placeholder="请填写与营业执照一致的企业名称" />
        </el-form-item>
        <el-form-item label="开户银行">
          <el-input v-model="form.bankName" placeholder="例如：招商银行高新支行" />
        </el-form-item>
        <el-form-item label="对公账号">
          <el-input v-model="form.bankAccount" placeholder="请填写企业对公银行账号" />
        </el-form-item>
        <el-form-item label="营业执照">
          <el-upload action="#" list-type="picture-card" :auto-upload="false">
            <el-icon><Upload /></el-icon>
          </el-upload>
          <div class="text-xs text-gray-400 mt-2">请上传清晰的营业执照扫描件，支持 JPG/PNG 格式，大小不超过 5MB</div>
        </el-form-item>
        <el-form-item v-if="verifyStatus === 'unbound'">
          <el-button type="primary" @click="submitForm">提交审核</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" class="base-card" v-if="verifyStatus === 'verified'">
        <template #header>
            <div class="card-header font-bold text-lg">
            <span>当前绑定账户信息</span>
            </div>
        </template>
        <el-descriptions :column="1" border>
            <el-descriptions-item label="主体类型">企业</el-descriptions-item>
            <el-descriptions-item label="企业全称">深圳市E-Charge新能源科技有限公司</el-descriptions-item>
            <el-descriptions-item label="开户银行">招商银行深圳分行高新园支行</el-descriptions-item>
            <el-descriptions-item label="对公账号">7559 **** **** 8888</el-descriptions-item>
            <el-descriptions-item label="认证状态">
                <el-tag type="success">已认证</el-tag>
            </el-descriptions-item>
        </el-descriptions>
    </el-card>
  </div>
</template>

<style scoped>
/* 样式已使用 Tailwind 类名替代 */
</style>
