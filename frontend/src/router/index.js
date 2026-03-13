import { createRouter, createWebHistory } from 'vue-router'

import { MODULES, ROLE_DEFAULT_ROUTE, hasModuleAccess } from '../config/permissions'

const getCurrentRole = () => localStorage.getItem('userRole') || 'operator'

const routes = [
  {
    path: '/',
    redirect: () => (getCurrentRole() === 'admin' ? '/admin/dashboard' : '/operator/dashboard'),
  },
  {
    path: '/admin',
    component: () => import('../layouts/MainLayout.vue'),
    redirect: '/admin/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'AdminDashboard',
        component: () => import('../views/shared/PlaceholderPage.vue'),
        meta: { title: '管理员概览', moduleCode: MODULES.OVERVIEW },
      },
      {
        path: 'todo/stations',
        name: 'StationAudit',
        component: () => import('../views/admin/todo/StationAudit.vue'),
        meta: { title: '电站审核', moduleCode: MODULES.STATION_REVIEW },
      },
      {
        path: 'todo/abnormal',
        name: 'AbnormalOrders',
        component: () => import('../views/admin/todo/AbnormalOrders.vue'),
        meta: { title: '异常订单干预', moduleCode: MODULES.ORDERS },
      },
      {
        path: 'todo/invoice',
        name: 'InvoiceManagement',
        component: () => import('../views/admin/todo/InvoiceManagement.vue'),
        meta: { title: '开票管理', moduleCode: MODULES.FINANCE_INVOICE },
      },
    ],
  },
  {
    path: '/operator',
    component: () => import('../layouts/MainLayout.vue'),
    redirect: '/operator/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'OperatorDashboard',
        component: () => import('../views/operator/dashboard/Index.vue'),
        meta: { title: '运营概览', moduleCode: MODULES.OVERVIEW },
      },
      {
        path: 'assets/stations',
        name: 'StationList',
        component: () => import('../views/operator/assets/StationList.vue'),
        meta: { title: '电站管理', moduleCode: MODULES.STATION_ASSET },
      },
      {
        path: 'assets/piles',
        name: 'PileManagement',
        component: () => import('../views/operator/assets/PileManagement.vue'),
        meta: { title: '设备实时监控', moduleCode: MODULES.STATION_ASSET },
      },
      {
        path: 'pricing',
        name: 'PricingSettings',
        component: () => import('../views/operator/pricing/PricingSettings.vue'),
        meta: { title: '分时电价设置', moduleCode: MODULES.STATION_PRICING },
      },
      {
        path: 'orders/history',
        name: 'HistoryOrders',
        component: () => import('../views/operator/orders/HistoryOrders.vue'),
        meta: { title: '历史订单', moduleCode: MODULES.ORDERS },
      },
      {
        path: 'orders/realtime',
        name: 'RealtimeOrders',
        component: () => import('../views/operator/orders/RealtimeOrders.vue'),
        meta: { title: '实时订单', moduleCode: MODULES.ORDERS },
      },
      {
        path: 'finance/settlement',
        name: 'Settlement',
        component: () => import('../views/operator/finance/Settlement.vue'),
        meta: { title: '收益对账', moduleCode: MODULES.FINANCE_SETTLEMENT },
      },
      {
        path: 'finance/cards',
        name: 'CardManagement',
        component: () => import('../views/operator/finance/CardManagement.vue'),
        meta: { title: '资质与绑卡', moduleCode: MODULES.FINANCE_CARD },
      },
    ],
  },
  {
    path: '/role-blueprint',
    name: 'RoleBlueprint',
    component: () => import('../views/shared/RoleBlueprint.vue'),
    meta: { title: '职责蓝图', moduleCode: MODULES.BLUEPRINT },
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/shared/PlaceholderPage.vue'),
    meta: { title: '系统设置', moduleCode: MODULES.SETTINGS },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach((to) => {
  const role = getCurrentRole()
  const moduleCode = to.meta?.moduleCode

  if (!moduleCode) return true

  if (hasModuleAccess(role, moduleCode)) {
    return true
  }

  return ROLE_DEFAULT_ROUTE[role] || '/operator/dashboard'
})

export default router
