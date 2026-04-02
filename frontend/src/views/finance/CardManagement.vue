<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import {
  CreditCard,
  RefreshRight,
  CircleCheck,
  Clock,
  WarningFilled,
  CloseBold,
  UploadFilled,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import PageSectionHeader from '../../components/console/PageSectionHeader.vue'
import MetricCard from '../../components/console/MetricCard.vue'
import EmptyStateBlock from '../../components/console/EmptyStateBlock.vue'
import http from '../../api/http'

const loading = ref(false)
const submitting = ref(false)
const formVisible = ref(false)

const cardInfo = reactive({
  operator_id: null,
  operator_name: '',
  operator_verified: false,
  audit_status: 'unbound',
  audit_status_text: '未绑定',
  cards: [],
  default_card: null,
  settlement_eligible: false,
  settlement_tip: '',
  settlement_notice: '',
})

const form = reactive({
  account_name: '',
  bank_name: '',
  bank_account: '',
  is_default: true,
})

const statusMeta = computed(() => {
  if (cardInfo.audit_status === 'approved') {
    return { type: 'success', title: '已通过', icon: CircleCheck, desc: '绑定卡审核通过，可进入 T+1 清分流程。' }
  }
  if (cardInfo.audit_status === 'pending') {
    return { type: 'info', title: '待审核', icon: Clock, desc: '绑卡资料已提交，平台审核通过后即可参与清分。' }
  }
  if (cardInfo.audit_status === 'rejected') {
    return { type: 'error', title: '已驳回', icon: CloseBold, desc: '请根据驳回原因补充资料并重新提交。' }
  }
  return { type: 'warning', title: '未绑定', icon: WarningFilled, desc: '尚未绑定收款卡，暂不具备 T+1 清分资格。' }
})

const stats = computed(() => [
  {
    label: '审核状态',
    value: cardInfo.audit_status_text || '未绑定',
    trend: '绑卡资料审核结果',
    trendLabel: '状态影响结算能力',
    tone:
      cardInfo.audit_status === 'approved'
        ? 'success'
        : cardInfo.audit_status === 'pending'
          ? 'info'
          : cardInfo.audit_status === 'rejected'
            ? 'danger'
            : 'warning',
    icon: CreditCard,
  },
  {
    label: '默认收款卡',
    value: cardInfo.default_card ? cardInfo.default_card.bank_account_masked : '未设置',
    trend: '用于平台打款',
    trendLabel: '仅审核通过卡可参与打款',
    tone: cardInfo.default_card ? 'primary' : 'warning',
    icon: CreditCard,
  },
  {
    label: '运营商认证',
    value: cardInfo.operator_verified ? '已认证' : '未认证',
    trend: '资格前置条件',
    trendLabel: '清分需要运营商认证通过',
    tone: cardInfo.operator_verified ? 'success' : 'danger',
    icon: CircleCheck,
  },
  {
    label: 'T+1 清分资格',
    value: cardInfo.settlement_eligible ? '已具备' : '未具备',
    trend: '结算资格判断',
    trendLabel: cardInfo.settlement_tip || '请完成绑卡与认证',
    tone: cardInfo.settlement_eligible ? 'success' : 'danger',
    icon: WarningFilled,
  },
])

const statusTagType = (status) => {
  if (Number(status) === 1) return 'success'
  if (Number(status) === 0) return 'warning'
  return 'danger'
}

const fetchCardInfo = async () => {
  loading.value = true
  try {
    const res = await http.get('/finance/cards')
    if (res?.data?.code === 200) {
      const payload = res.data.data || {}
      Object.assign(cardInfo, {
        operator_id: payload.operator_id,
        operator_name: payload.operator_name || '',
        operator_verified: Boolean(payload.operator_verified),
        audit_status: payload.audit_status || 'unbound',
        audit_status_text: payload.audit_status_text || '未绑定',
        cards: Array.isArray(payload.cards) ? payload.cards : [],
        default_card: payload.default_card || null,
        settlement_eligible: Boolean(payload.settlement_eligible),
        settlement_tip: payload.settlement_tip || '',
        settlement_notice: payload.settlement_notice || '',
      })
      return
    }
    ElMessage.error(res?.data?.message || '加载绑卡信息失败')
  } catch (error) {
    ElMessage.error('加载绑卡信息失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const openSubmitDialog = () => {
  form.account_name = ''
  form.bank_name = ''
  form.bank_account = ''
  form.is_default = !cardInfo.cards.length
  formVisible.value = true
}

const submitForm = async () => {
  if (!form.account_name.trim() || !form.bank_name.trim() || form.bank_account.replace(/\s+/g, '').length < 8) {
    ElMessage.warning('请填写完整且有效的绑卡资料')
    return
  }

  submitting.value = true
  try {
    const res = await http.post('/finance/cards', {
      account_name: form.account_name,
      bank_name: form.bank_name,
      bank_account: form.bank_account,
      is_default: form.is_default,
    })
    if (res?.data?.code === 200) {
      ElMessage.success(res.data.message || '提交成功')
      formVisible.value = false
      await fetchCardInfo()
      return
    }
    ElMessage.error(res?.data?.message || '提交失败')
  } catch (error) {
    ElMessage.error('提交失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

onMounted(fetchCardInfo)
</script>

<template>
  <div class="page-shell card-management-page">
    <PageSectionHeader
      eyebrow="Bank Card Management"
      title="绑卡管理"
      description="管理运营商收款银行卡与审核状态，作为 T+1 清分资格的核心前置条件。"
      chip="运营商财务模块"
    >
      <template #actions>
        <el-button :icon="RefreshRight" :loading="loading" @click="fetchCardInfo">刷新状态</el-button>
        <el-button type="primary" @click="openSubmitDialog">提交绑卡资料</el-button>
      </template>
    </PageSectionHeader>

    <el-alert
      :type="statusMeta.type"
      :title="`当前绑卡状态：${statusMeta.title}`"
      :description="`${statusMeta.desc} 绑卡成功后才可启动 T+1 清分；如遇法定节假日，打款顺延至下一工作日。`"
      show-icon
      :closable="false"
      class="status-alert"
    />

    <section class="stats-grid stats-grid--card">
      <MetricCard
        v-for="item in stats"
        :key="item.label"
        :label="item.label"
        :value="item.value"
        :trend="item.trend"
        :trend-label="item.trendLabel"
        :tone="item.tone"
        :icon="item.icon"
      />
    </section>

    <section class="panel-grid panel-grid--wide">
      <article class="page-panel surface-card" v-loading="loading">
        <div class="panel-heading">
          <div>
            <h3 class="panel-heading__title">默认收款卡</h3>
            <p class="panel-heading__desc">平台打款默认使用该银行卡，且需审核通过才可用于清分。</p>
          </div>
        </div>

        <div v-if="cardInfo.default_card" class="default-card">
          <div class="default-card__item">
            <span>开户名</span>
            <strong>{{ cardInfo.default_card.account_name }}</strong>
          </div>
          <div class="default-card__item">
            <span>开户银行</span>
            <strong>{{ cardInfo.default_card.bank_name }}</strong>
          </div>
          <div class="default-card__item">
            <span>银行卡号</span>
            <strong>{{ cardInfo.default_card.bank_account_masked }}</strong>
          </div>
          <div class="default-card__item">
            <span>审核状态</span>
            <el-tag :type="statusTagType(cardInfo.default_card.bind_status)" size="small">
              {{ cardInfo.default_card.bind_status_text }}
            </el-tag>
          </div>
        </div>

        <EmptyStateBlock
          v-else-if="!loading"
          title="尚未配置默认收款卡"
          description="请先提交绑卡资料并通过审核，才可进入 T+1 清分。"
        />

        <div class="settlement-note">
          <p><strong>清分资格：</strong>{{ cardInfo.settlement_eligible ? '已具备' : '暂不具备' }}</p>
          <p><strong>资格说明：</strong>{{ cardInfo.settlement_tip || '请补全认证与绑卡信息' }}</p>
          <p><strong>规则提示：</strong>{{ cardInfo.settlement_notice || '绑卡审核通过后可参与 T+1 清分，节假日顺延。' }}</p>
        </div>
      </article>

      <article class="page-panel surface-card table-shell" v-loading="loading">
        <div class="panel-heading">
          <div>
            <h3 class="panel-heading__title">绑卡记录</h3>
            <p class="panel-heading__desc">查看当前运营商所有绑卡记录与审核状态。</p>
          </div>
        </div>

        <el-table v-if="cardInfo.cards.length" :data="cardInfo.cards" stripe border>
          <el-table-column prop="account_name" label="开户名" min-width="120" />
          <el-table-column prop="bank_name" label="开户银行" min-width="160" />
          <el-table-column prop="bank_account_masked" label="银行卡号" min-width="140" />
          <el-table-column label="默认卡" width="90" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.is_default" type="success" size="small">默认</el-tag>
              <span v-else class="text-muted">-</span>
            </template>
          </el-table-column>
          <el-table-column label="审核状态" width="110" align="center">
            <template #default="{ row }">
              <el-tag :type="statusTagType(row.bind_status)" size="small">{{ row.bind_status_text }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="提交时间" min-width="150" />
          <el-table-column prop="updated_at" label="更新时间" min-width="150" />
        </el-table>

        <EmptyStateBlock
          v-else-if="!loading"
          title="暂无绑卡记录"
          description="点击“提交绑卡资料”后，记录会显示在此处。"
        />
      </article>
    </section>

    <el-dialog v-model="formVisible" title="提交绑卡资料" width="560px">
      <el-form label-width="110px">
        <el-form-item label="开户名">
          <el-input v-model="form.account_name" placeholder="请填写对公账户开户名" />
        </el-form-item>
        <el-form-item label="开户银行">
          <el-input v-model="form.bank_name" placeholder="例如：招商银行深圳分行" />
        </el-form-item>
        <el-form-item label="银行卡号">
          <el-input v-model="form.bank_account" placeholder="请输入银行卡号" />
        </el-form-item>
        <el-form-item label="设为默认卡">
          <el-switch v-model="form.is_default" />
        </el-form-item>
        <el-form-item label="资料附件">
          <el-upload action="#" :auto-upload="false" list-type="text">
            <el-button :icon="UploadFilled">上传证明材料（可选）</el-button>
          </el-upload>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">提交审核</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.card-management-page {
  padding-bottom: 10px;
}

.status-alert {
  border-radius: 10px;
}

.stats-grid--card {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.default-card {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.default-card__item {
  padding: 12px;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.9), rgba(246, 250, 255, 0.9));
}

.default-card__item span {
  display: block;
  color: var(--color-text-3);
  font-size: 12px;
}

.default-card__item strong {
  display: block;
  margin-top: 8px;
  color: var(--color-text);
}

.settlement-note {
  margin-top: 14px;
  padding: 12px;
  border-radius: 12px;
  background: rgba(47, 116, 255, 0.06);
  border: 1px solid rgba(47, 116, 255, 0.14);
  color: var(--color-text-2);
  line-height: 1.75;
  font-size: 13px;
}

.text-muted {
  color: #909399;
}

@media (max-width: 1280px) {
  .stats-grid--card {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .stats-grid--card,
  .default-card {
    grid-template-columns: 1fr;
  }
}
</style>
