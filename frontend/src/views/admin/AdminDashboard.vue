<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  IconAlertTriangle,
  IconArrowRight,
  IconBolt,
  IconBuilding,
  IconReceipt,
  IconWallet,
} from '@tabler/icons-vue'

import { fetchOverviewSummary } from '../../api/overview'

const router = useRouter()

const loading = ref(false)
const summary = ref({
  today_orders: 0,
  today_revenue: 0,
  online_piles: 0,
  total_piles: 0,
  active_users: 0,
  new_users_month: 0,
})

const cards = computed(() => [
  {
    title: '今日平台订单',
    value: summary.value.today_orders.toLocaleString(),
    note: '用于观察全网交易活跃度',
    icon: IconBolt,
    tone: 'blue',
  },
  {
    title: '今日平台收入',
    value: `¥${Number(summary.value.today_revenue || 0).toLocaleString()}`,
    note: '结合清分执行把控资金节奏',
    icon: IconWallet,
    tone: 'emerald',
  },
  {
    title: '在线充电桩',
    value: `${summary.value.online_piles}/${summary.value.total_piles}`,
    note: '辅助判断设备健康与故障分布',
    icon: IconBuilding,
    tone: 'amber',
  },
  {
    title: '活跃用户数',
    value: summary.value.active_users.toLocaleString(),
    note: `本月新增 ${summary.value.new_users_month} 人`,
    icon: IconReceipt,
    tone: 'violet',
  },
])

const shortcuts = [
  {
    title: '电站上架审批',
    description: '复用现有电站审核页，集中处理待上线站点。',
    route: '/admin/institutions/stations',
  },
  {
    title: '清分结算执行',
    description: '复用全局清分页，保留手动执行与批次回看能力。',
    route: '/admin/finance',
  },
  {
    title: '发票合规抽查',
    description: '复用开票处理页，继续承接发票审核动作。',
    route: '/admin/finance/invoices',
  },
  {
    title: '全局订单查询',
    description: '先承接原历史订单页，后续可继续扩展更多平台维度筛选。',
    route: '/admin/orders',
  },
]

const todoList = [
  '运营商入驻审核页已挂到新的管理端结构，当前先用占位页承接完整菜单。',
  '用户管理、营销合规、系统参数这三块已预留正式入口，便于后续继续开发。',
  '旧项目里可复用的订单、清分、开票、电站审核页都已经迁移到更合适的位置。',
]

const loadSummary = async () => {
  loading.value = true
  try {
    const res = await fetchOverviewSummary()
    summary.value = { ...summary.value, ...(res?.data || {}) }
  } catch (error) {
    console.error(error)
    ElMessage.error('管理端概览加载失败，已展示默认数据骨架')
  } finally {
    loading.value = false
  }
}

onMounted(loadSummary)
</script>

<template>
  <div class="admin-dashboard">
    <section class="hero surface-card">
      <div>
        <p class="hero__eyebrow">Admin Console</p>
        <h1 class="hero__title">平台治理工作台</h1>
        <p class="hero__desc">
          这一层只承接平台管理员视角，聚焦入驻审核、订单监管、清分执行与系统规则控制。
        </p>
      </div>
      <div class="hero__badge">
        <IconAlertTriangle :size="18" />
        <span>高权限视角</span>
      </div>
    </section>

    <section class="metrics">
      <article
        v-for="card in cards"
        :key="card.title"
        class="metric surface-card"
        :class="`metric--${card.tone}`"
        v-loading="loading"
      >
        <div class="metric__icon">
          <component :is="card.icon" :size="20" />
        </div>
        <div>
          <p class="metric__title">{{ card.title }}</p>
          <h3 class="metric__value">{{ card.value }}</h3>
          <p class="metric__note">{{ card.note }}</p>
        </div>
      </article>
    </section>

    <section class="content-grid">
      <article class="panel surface-card">
        <div class="panel__header">
          <div>
            <h3 class="panel__title">快捷入口</h3>
            <p class="panel__desc">把现有可复用页面优先迁移到平台治理主链路。</p>
          </div>
        </div>
        <div class="shortcut-list">
          <button
            v-for="item in shortcuts"
            :key="item.route"
            class="shortcut"
            type="button"
            @click="router.push(item.route)"
          >
            <div>
              <div class="shortcut__title">{{ item.title }}</div>
              <div class="shortcut__desc">{{ item.description }}</div>
            </div>
            <IconArrowRight :size="18" />
          </button>
        </div>
      </article>

      <article class="panel surface-card">
        <div class="panel__header">
          <div>
            <h3 class="panel__title">重构说明</h3>
            <p class="panel__desc">当前这一版先保证导航完整、路由稳定、已开发页面就位。</p>
          </div>
        </div>
        <ul class="todo-list">
          <li v-for="item in todoList" :key="item">{{ item }}</li>
        </ul>
      </article>
    </section>
  </div>
</template>

<style scoped>
.admin-dashboard {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hero {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 24px;
}

.hero__eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-text-3);
}

.hero__title {
  margin: 0;
  font-size: 28px;
  line-height: 1.15;
}

.hero__desc {
  margin: 10px 0 0;
  max-width: 720px;
  color: var(--color-text-2);
  line-height: 1.6;
}

.hero__badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: fit-content;
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(245, 108, 108, 0.1);
  color: #d44949;
}

.metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.metric {
  display: flex;
  gap: 14px;
  padding: 18px;
}

.metric__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 14px;
}

.metric--blue .metric__icon {
  background: rgba(64, 158, 255, 0.12);
  color: #409eff;
}

.metric--emerald .metric__icon {
  background: rgba(46, 204, 113, 0.12);
  color: #1f9d61;
}

.metric--amber .metric__icon {
  background: rgba(230, 162, 60, 0.12);
  color: #d28a1d;
}

.metric--violet .metric__icon {
  background: rgba(116, 75, 162, 0.12);
  color: #744ba2;
}

.metric__title,
.metric__note {
  margin: 0;
  color: var(--color-text-3);
}

.metric__value {
  margin: 6px 0;
  font-size: 26px;
}

.content-grid {
  display: grid;
  grid-template-columns: 1.3fr 1fr;
  gap: 16px;
}

.panel {
  padding: 18px;
}

.panel__header {
  margin-bottom: 14px;
}

.panel__title {
  margin: 0;
  font-size: 18px;
}

.panel__desc {
  margin: 6px 0 0;
  color: var(--color-text-3);
}

.shortcut-list {
  display: grid;
  gap: 12px;
}

.shortcut {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  width: 100%;
  padding: 14px 16px;
  border: 1px solid var(--color-border);
  border-radius: 14px;
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.shortcut:hover {
  border-color: rgba(64, 158, 255, 0.35);
  background: rgba(64, 158, 255, 0.04);
}

.shortcut__title {
  font-weight: 700;
}

.shortcut__desc {
  margin-top: 6px;
  color: var(--color-text-3);
  line-height: 1.5;
}

.todo-list {
  margin: 0;
  padding-left: 18px;
  color: var(--color-text-2);
  line-height: 1.8;
}

@media (max-width: 1200px) {
  .metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .hero {
    flex-direction: column;
    padding: 18px;
  }

  .metrics {
    grid-template-columns: 1fr;
  }
}
</style>
