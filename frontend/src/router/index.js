import { createRouter, createWebHistory } from 'vue-router'

import MainLayout from '../layouts/MainLayout.vue'
import PlaceholderPage from '../views/PlaceholderPage.vue'
import AdminDashboard from '../views/admin/AdminDashboard.vue'
import DashboardView from '../views/Dashboard.vue'
import {
  getRoleByPath,
  getStoredRole,
  resolveRoleDefaultRoute,
  ROLES,
  setStoredRole,
} from '../config/permissions'

const roleAwareRedirect = (mapping) => {
  const role = getStoredRole()
  return mapping[role] || mapping.default || resolveRoleDefaultRoute(role)
}

const makePlaceholderMeta = (title, description) => ({
  title,
  placeholderDescription: description,
})

const routes = [
  {
    path: '/',
    redirect: () => resolveRoleDefaultRoute(getStoredRole()),
  },
  {
    path: '/admin',
    component: MainLayout,
    meta: { role: ROLES.ADMIN },
    children: [
      {
        path: '',
        name: 'AdminDashboard',
        component: AdminDashboard,
        meta: {
          role: ROLES.ADMIN,
          title: '平台工作台',
          section: '概览',
        },
      },
      {
        path: 'institutions',
        name: 'AdminInstitutions',
        component: PlaceholderPage,
        meta: {
          role: ROLES.ADMIN,
          section: '机构管理',
          ...makePlaceholderMeta('运营商入驻审核', '此页面待开发，将承接运营商准入、资质复核与审核流转。'),
        },
      },
      {
        path: 'institutions/stations',
        name: 'AdminInstitutionStations',
        component: () => import('../views/admin/todo/StationAudit.vue'),
        meta: {
          role: ROLES.ADMIN,
          title: '电站上架审批',
          section: '机构管理',
        },
      },
      {
        path: 'orders',
        name: 'AdminOrders',
        component: () => import('../views/orders/HistoryOrders.vue'),
        meta: {
          role: ROLES.ADMIN,
          title: '全局订单查询',
          section: '订单监管',
        },
      },
      {
        path: 'orders/anomalies',
        name: 'AdminOrderAnomalies',
        component: () => import('../views/orders/AbnormalOrders.vue'),
        meta: {
          role: ROLES.ADMIN,
          title: '异常订单监管',
          section: '订单监管',
        },
      },
      {
        path: 'finance',
        name: 'AdminFinance',
        component: () => import('../views/admin/GlobalSettle.vue'),
        meta: {
          role: ROLES.ADMIN,
          title: '清分结算执行',
          section: '资金清分',
        },
      },
      {
        path: 'finance/invoices',
        name: 'AdminFinanceInvoices',
        component: () => import('../views/finance/InvoiceManagement.vue'),
        meta: {
          role: ROLES.ADMIN,
          title: '发票合规抽查',
          section: '资金清分',
        },
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: PlaceholderPage,
        meta: {
          role: ROLES.ADMIN,
          section: '用户管理',
          ...makePlaceholderMeta('用户列表', '此页面待开发，后续可接入全平台用户检索、画像与状态管控。'),
        },
      },
      {
        path: 'users/blacklist',
        name: 'AdminUsersBlacklist',
        component: PlaceholderPage,
        meta: {
          role: ROLES.ADMIN,
          section: '用户管理',
          ...makePlaceholderMeta('封禁用户管理', '此页面待开发，后续用于沉淀封禁策略、申诉处理与恢复流程。'),
        },
      },
      {
        path: 'marketing',
        name: 'AdminMarketing',
        component: PlaceholderPage,
        meta: {
          role: ROLES.ADMIN,
          section: '系统配置',
          ...makePlaceholderMeta('营销合规审计', '此页面待开发，后续用于平台级营销规则稽核与活动合规巡检。'),
        },
      },
      {
        path: 'settings',
        name: 'AdminSettings',
        component: () => import('../views/RoleBlueprint.vue'),
        meta: {
          role: ROLES.ADMIN,
          title: '权限控制',
          section: '系统配置',
        },
      },
      {
        path: 'settings/params',
        name: 'AdminSettingsParams',
        component: PlaceholderPage,
        meta: {
          role: ROLES.ADMIN,
          section: '系统配置',
          ...makePlaceholderMeta('系统参数设置', '此页面待开发，后续可挂接站点审核策略、清分参数与通知模板。'),
        },
      },
    ],
  },
  {
    path: '/operator',
    component: MainLayout,
    meta: { role: ROLES.OPERATOR },
    children: [
      {
        path: '',
        name: 'OperatorDashboard',
        component: DashboardView,
        meta: {
          role: ROLES.OPERATOR,
          title: '运营工作台',
          section: '概览',
        },
      },
      {
        path: 'stations',
        name: 'OperatorStations',
        component: () => import('../views/stations/StationList.vue'),
        meta: {
          role: ROLES.OPERATOR,
          title: '站点管理',
          section: '资产管理',
        },
      },
      {
        path: 'stations/chargers',
        name: 'OperatorStationsChargers',
        component: () => import('../views/stations/PileManagement.vue'),
        meta: {
          role: ROLES.OPERATOR,
          title: '设备状态总览',
          section: '资产管理',
        },
      },
      {
        path: 'billing',
        name: 'OperatorBilling',
        component: () => import('../views/stations/PricingSettings.vue'),
        meta: {
          role: ROLES.OPERATOR,
          title: '电价设置',
          section: '计费管理',
        },
      },
      {
        path: 'billing/templates',
        name: 'OperatorBillingTemplates',
        component: PlaceholderPage,
        meta: {
          role: ROLES.OPERATOR,
          section: '计费管理',
          ...makePlaceholderMeta('计费模板管理', '此页面待开发，后续可沉淀尖峰平谷模板、复制模板和模板分配。'),
        },
      },
      {
        path: 'orders',
        name: 'OperatorOrders',
        component: () => import('../views/orders/HistoryOrders.vue'),
        meta: {
          role: ROLES.OPERATOR,
          title: '历史订单',
          section: '订单管理',
        },
      },
      {
        path: 'orders/realtime',
        name: 'OperatorOrdersRealtime',
        component: () => import('../views/orders/RealtimeOrders.vue'),
        meta: {
          role: ROLES.OPERATOR,
          title: '实时订单监控',
          section: '订单管理',
        },
      },
      {
        path: 'finance',
        name: 'OperatorFinance',
        component: () => import('../views/finance/Settlement.vue'),
        meta: {
          role: ROLES.OPERATOR,
          title: '收益对账',
          section: '财务管理',
        },
      },
      {
        path: 'finance/bank-card',
        name: 'OperatorFinanceBankCard',
        component: () => import('../views/finance/CardManagement.vue'),
        meta: {
          role: ROLES.OPERATOR,
          title: '绑卡管理',
          section: '财务管理',
        },
      },
      {
        path: 'finance/invoices',
        name: 'OperatorFinanceInvoices',
        component: () => import('../views/finance/InvoiceManagement.vue'),
        meta: {
          role: ROLES.OPERATOR,
          title: '开票管理',
          section: '财务管理',
        },
      },
      {
        path: 'customers',
        name: 'OperatorCustomers',
        component: PlaceholderPage,
        meta: {
          role: ROLES.OPERATOR,
          section: '客户管理',
          ...makePlaceholderMeta('车队与白名单', '此页面待开发，后续可整合车队、白名单与客户分层运营入口。'),
        },
      },
      {
        path: 'customers/fleets',
        name: 'OperatorCustomerFleets',
        component: PlaceholderPage,
        meta: {
          role: ROLES.OPERATOR,
          section: '客户管理',
          ...makePlaceholderMeta('专属用户管理', '此页面待开发，后续用于维护专属机构下的车队、账号与授权关系。'),
        },
      },
      {
        path: 'customers/tags',
        name: 'OperatorCustomerTags',
        component: PlaceholderPage,
        meta: {
          role: ROLES.OPERATOR,
          section: '客户管理',
          ...makePlaceholderMeta('标签管理', '此页面待开发，后续用于会员标签、人群筛选与精细化触达。'),
        },
      },
      {
        path: 'marketing',
        name: 'OperatorMarketing',
        component: PlaceholderPage,
        meta: {
          role: ROLES.OPERATOR,
          section: '营销管理',
          ...makePlaceholderMeta('折扣优惠', '此页面待开发，后续用于折扣活动、渠道投放与效果回收。'),
        },
      },
      {
        path: 'marketing/coupons',
        name: 'OperatorMarketingCoupons',
        component: PlaceholderPage,
        meta: {
          role: ROLES.OPERATOR,
          section: '营销管理',
          ...makePlaceholderMeta('优惠券发放', '此页面待开发，后续用于发券策略、批量投放和核销追踪。'),
        },
      },
      {
        path: 'settings',
        name: 'OperatorSettings',
        component: PlaceholderPage,
        meta: {
          role: ROLES.OPERATOR,
          section: '系统',
          ...makePlaceholderMeta('系统设置', '此页面待开发，后续用于企业资料、通知开关与角色成员维护。'),
        },
      },
    ],
  },
  {
    path: '/overview',
    redirect: () => roleAwareRedirect({ admin: '/admin', operator: '/operator' }),
  },
  {
    path: '/orders/history',
    redirect: () => roleAwareRedirect({ admin: '/admin/orders', operator: '/operator/orders' }),
  },
  {
    path: '/orders/realtime',
    redirect: () => roleAwareRedirect({ admin: '/admin/orders', operator: '/operator/orders/realtime' }),
  },
  {
    path: '/orders/abnormal',
    redirect: '/admin/orders/anomalies',
  },
  {
    path: '/finance/cards',
    redirect: '/operator/finance/bank-card',
  },
  {
    path: '/finance/settlement',
    redirect: '/operator/finance',
  },
  {
    path: '/finance/global-settle',
    redirect: '/admin/finance',
  },
  {
    path: '/finance/invoice',
    redirect: () => roleAwareRedirect({
      admin: '/admin/finance/invoices',
      operator: '/operator/finance/invoices',
    }),
  },
  {
    path: '/stations/list',
    redirect: '/operator/stations',
  },
  {
    path: '/stations/piles',
    redirect: '/operator/stations/chargers',
  },
  {
    path: '/stations/pricing',
    redirect: '/operator/billing',
  },
  {
    path: '/stations/review',
    redirect: '/admin/institutions/stations',
  },
  {
    path: '/organizations/operators',
    redirect: '/admin/institutions',
  },
  {
    path: '/organizations/exclusive',
    redirect: '/operator/customers/fleets',
  },
  {
    path: '/users/fleet',
    redirect: '/operator/customers',
  },
  {
    path: '/users/whitelist',
    redirect: '/operator/customers',
  },
  {
    path: '/marketing/tags',
    redirect: '/operator/customers/tags',
  },
  {
    path: '/marketing/discounts',
    redirect: '/operator/marketing',
  },
  {
    path: '/role-blueprint',
    redirect: () => roleAwareRedirect({ admin: '/admin/settings', operator: '/operator/settings' }),
  },
  {
    path: '/settings',
    redirect: () => roleAwareRedirect({ admin: '/admin/settings', operator: '/operator/settings' }),
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach((to) => {
  const roleFromPath = getRoleByPath(to.path)
  if (roleFromPath) {
    setStoredRole(roleFromPath)
    return true
  }

  if (to.path === '/') {
    return resolveRoleDefaultRoute(getStoredRole())
  }

  return true
})

export default router
