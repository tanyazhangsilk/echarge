<script setup>
import { computed } from 'vue'

const role = computed(() => localStorage.getItem('userRole') || 'operator')

const kpiMap = {
  admin: ['审核通过率', '异常工单闭环时长', '平台结算达成率', '发票合规率'],
  operator: ['充电订单量', '站点利用率', '应收到账率', '会员留存率'],
}

const processFlow = [
  {
    title: '订单履约',
    steps: '下单 -> 启充 -> 停充 -> 结算 -> 对账 -> 开票',
    owner: '运营商（异常升级到平台管理员）',
  },
  {
    title: '站点上架',
    steps: '运营商提交资质 -> 管理员审核 -> 站桩上线 -> 运营监控',
    owner: '管理员审核，运营商维护',
  },
  {
    title: '营销投放',
    steps: '标签圈人 -> 折扣规则 -> 活动生效 -> 效果复盘',
    owner: '运营商主责，管理员只看合规',
  },
]
</script>

<template>
  <div class="blueprint-page">
    <el-alert
      title="先定边界，再做页面：管理员只做平台治理，运营商只做经营动作。"
      type="success"
      :closable="false"
      show-icon
      class="mb-16"
    />

    <el-row :gutter="16" class="mb-16">
      <el-col :md="12" :sm="24">
        <el-card shadow="never">
          <template #header>
            <span>当前角色北极星指标（{{ role === 'admin' ? '管理员' : '运营商' }}）</span>
          </template>
          <el-tag v-for="item in kpiMap[role]" :key="item" class="mr-8 mb-8">{{ item }}</el-tag>
        </el-card>
      </el-col>
      <el-col :md="12" :sm="24">
        <el-card shadow="never">
          <template #header>
            <span>推荐的菜单拆分原则</span>
          </template>
          <ul>
            <li>同一页面只服务一个角色，避免字段和按钮条件分支爆炸。</li>
            <li>共享数据（订单、发票）可以共表，但操作入口分角色独立。</li>
            <li>跨角色动作统一走“待办中心”，不要在业务页互相塞按钮。</li>
          </ul>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="mb-16">
      <template #header>
        <span>职责矩阵（建议你按这个再拆页面）</span>
      </template>
      <el-table :data="[
        { domain: '订单管理', admin: '看全局、管异常规则', operator: '看自有订单、处理售后', note: '订单详情字段可共用' },
        { domain: '财务管理', admin: '执行清分、发票监管', operator: '绑卡、对账、开票申请', note: 'T+1触发由绑卡状态决定' },
        { domain: '电站电桩', admin: '资质审核/封禁', operator: '站桩维护、电价策略', note: '上架需审核通过' },
        { domain: '机构管理', admin: '运营商准入与信息校验', operator: '维护自有机构树', note: '专属机构需绑定专属用户' },
        { domain: '用户营销', admin: '合规审计', operator: '车队/白名单/标签/折扣', note: '优惠动作都归运营商' },
      ]" border>
        <el-table-column prop="domain" label="模块" width="140" />
        <el-table-column prop="admin" label="管理员" />
        <el-table-column prop="operator" label="运营商" />
        <el-table-column prop="note" label="设计要点" />
      </el-table>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <span>核心流程（用于梳理状态机）</span>
      </template>
      <el-timeline>
        <el-timeline-item v-for="item in processFlow" :key="item.title" :timestamp="item.owner" placement="top">
          <h4>{{ item.title }}</h4>
          <p>{{ item.steps }}</p>
        </el-timeline-item>
      </el-timeline>
    </el-card>
  </div>
</template>

<style scoped>
.blueprint-page { display: flex; flex-direction: column; }
.mb-16 { margin-bottom: 16px; }
.mb-8 { margin-bottom: 8px; }
.mr-8 { margin-right: 8px; }
ul { margin: 0; padding-left: 18px; line-height: 1.9; color: var(--text-regular); }
</style>
