import { createRouter, createWebHistory } from 'vue-router'

import DashboardView from '../views/Dashboard.vue'
import { MODULES, ROLE_DEFAULT_ROUTE, hasModuleAccess } from '../config/permissions'

const getCurrentRole = () => localStorage.getItem('userRole') || 'operator'

const routes = [
  {
    path: '/',
    redirect: () => ROLE_DEFAULT_ROUTE[getCurrentRole()] || '/overview',
  },
  {
    path: '/overview',
    name: 'Overview',
    component: DashboardView,
    meta: {
      title: '概览',
      moduleCode: MODULES.OVERVIEW,
    },
  },
  {
    path: '/orders',
    name: 'Orders',
    component: () => import('../views/orders/OrdersLayout.vue'),
    redirect: '/orders/history',
    children: [
      {
        path: 'history',
        name: 'HistoryOrders',
        component: () => import('../views/orders/HistoryOrders.vue'),
        meta: { title: '历史订单', moduleCode: MODULES.ORDERS },
      },
      {
        path: 'realtime',
        name: 'RealtimeOrders',
        component: () => import('../views/orders/RealtimeOrders.vue'),
        meta: { title: '实时订单', moduleCode: MODULES.ORDERS },
      },
      {
        path: 'abnormal',
        name: 'AbnormalOrders',
        component: () => import('../views/orders/AbnormalOrders.vue'),
        meta: { title: '异常订单', moduleCode: MODULES.ORDERS },
      },
    ],
    meta: { title: '订单管理', moduleCode: MODULES.ORDERS },
  },
  {
    path: '/finance',
    name: 'Finance',
    component: () => import('../views/finance/FinanceLayout.vue'),
    redirect: '/finance/cards',
    children: [
      {
        path: 'cards',
        name: 'CardManagement',
        component: () => import('../views/finance/CardManagement.vue'),
        meta: { title: '资质与绑卡', moduleCode: MODULES.FINANCE_CARD },
      },
      {
        path: 'settlement',
        name: 'Settlement',
        component: () => import('../views/finance/Settlement.vue'),
        meta: { title: '收益对账', moduleCode: MODULES.FINANCE_SETTLEMENT },
      },
      {
        path: 'global-settle',
        name: 'GlobalSettle',
        component: () => import('../views/admin/GlobalSettle.vue'),
        meta: { title: '平台清分执行', moduleCode: MODULES.FINANCE_GLOBAL_SETTLE },
      },
      {
        path: 'invoice',
        name: 'InvoiceManagement',
        component: () => import('../views/finance/InvoiceManagement.vue'),
        meta: { title: '开票管理', moduleCode: MODULES.FINANCE_INVOICE },
      },
    ],
    meta: { title: '财务管理' },
  },
  {
    path: '/stations',
    name: 'Stations',
    component: () => import('../views/stations/StationsLayout.vue'),
    redirect: '/stations/list',
    children: [
      {
        path: 'list',
        name: 'StationList',
        component: () => import('../views/stations/StationList.vue'),
        meta: { title: '电站列表', moduleCode: MODULES.STATION_ASSET },
      },
      {
        path: 'piles',
        name: 'PileManagement',
        component: () => import('../views/stations/PileManagement.vue'),
        meta: { title: '电桩管理', moduleCode: MODULES.STATION_ASSET },
      },
      {
        path: 'pricing',
        name: 'PricingSettings',
        component: () => import('../views/stations/PricingSettings.vue'),
        meta: { title: '电价设置', moduleCode: MODULES.STATION_PRICING },
      },
      {
        path: 'review',
        name: 'StationReview',
        component: () => import('../views/admin/todo/StationAudit.vue'),
        meta: { title: '电站上线审核', moduleCode: MODULES.STATION_REVIEW },
      },
      {
        path: 'audit',
        redirect: '/stations/review',
      },
    ],
    meta: { title: '电桩电站管理' },
  },
  {
    path: '/organizations/operators',
    name: 'OrganizationOperators',
    component: () => import('../views/PlaceholderPage.vue'),
    meta: { title: '运营商入驻审核', moduleCode: MODULES.ORG_OPERATOR_AUDIT },
  },
  {
    path: '/organizations/exclusive',
    name: 'OrganizationExclusive',
    component: () => import('../views/PlaceholderPage.vue'),
    meta: { title: '专属机构', moduleCode: MODULES.ORG_EXCLUSIVE },
  },
  {
    path: '/users/fleet',
    name: 'UserFleet',
    component: () => import('../views/PlaceholderPage.vue'),
    meta: { title: '车队管理', moduleCode: MODULES.USER_FLEET },
  },
  {
    path: '/users/whitelist',
    name: 'UserWhitelist',
    component: () => import('../views/PlaceholderPage.vue'),
    meta: { title: '白名单管理', moduleCode: MODULES.USER_WHITELIST },
  },
  {
    path: '/marketing/tags',
    name: 'MarketingTags',
    component: () => import('../views/PlaceholderPage.vue'),
    meta: { title: '标签管理', moduleCode: MODULES.MARKETING },
  },
  {
    path: '/marketing/discounts',
    name: 'MarketingDiscounts',
    component: () => import('../views/PlaceholderPage.vue'),
    meta: { title: '折扣活动', moduleCode: MODULES.MARKETING },
  },
  {
    path: '/role-blueprint',
    name: 'RoleBlueprint',
    component: () => import('../views/RoleBlueprint.vue'),
    meta: { title: '职责蓝图', moduleCode: MODULES.BLUEPRINT },
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/PlaceholderPage.vue'),
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

  return ROLE_DEFAULT_ROUTE[role] || '/overview'
})

export default router
