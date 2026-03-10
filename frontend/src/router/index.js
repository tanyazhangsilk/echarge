import { createRouter, createWebHistory } from 'vue-router'

import DashboardView from '../views/Dashboard.vue'

const routes = [
  {
    path: '/',
    redirect: '/overview',
  },
  {
    path: '/overview',
    name: 'Overview',
    component: DashboardView,
    meta: {
      title: '概览',
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
        meta: {
          title: '历史订单',
        },
      },
      {
        path: 'realtime',
        name: 'RealtimeOrders',
        component: () => import('../views/orders/RealtimeOrders.vue'),
        meta: {
          title: '实时订单',
        },
      },
      {
        path: 'abnormal',
        name: 'AbnormalOrders',
        component: () => import('../views/orders/AbnormalOrders.vue'),
        meta: {
          title: '异常订单',
        },
      }
    ],
    meta: {
      title: '订单管理',
    },
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
        meta: { title: '绑卡管理' }
      },
      {
        path: 'settlement',
        name: 'Settlement',
        component: () => import('../views/finance/Settlement.vue'),
        meta: { title: '收益对账' }
      },
      {
        path: 'invoice',
        name: 'InvoiceManagement',
        component: () => import('../views/finance/InvoiceManagement.vue'),
        meta: { title: '开票管理' }
      }
      ],
    meta: {
      title: '财务管理',
    },
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
        meta: { title: '电站列表' }
      },
      {
        path: 'piles',
        name: 'PileManagement',
        component: () => import('../views/stations/PileManagement.vue'),
        meta: { title: '电桩管理' }
      },
      {
        path: 'pricing',
        name: 'PricingSettings',
        component: () => import('../views/stations/PricingSettings.vue'),
        meta: { title: '电价设置' }
      },
      {
        path: 'review',
        name: 'ReviewManagement',
        component: () => import('../views/stations/ReviewManagement.vue'),
        meta: { title: '审核管理' }
      },
    ],
    meta: {
      title: '电桩电站管理',
    },
  },
  {
    path: '/organizations',
    name: 'Organizations',
    component: () => import('../views/PlaceholderPage.vue'),
    meta: {
      title: '机构管理',
    },
  },
  {
    path: '/users',
    name: 'Users',
    component: () => import('../views/PlaceholderPage.vue'),
    meta: {
      title: '用户管理',
    },
  },
  {
    path: '/marketing',
    name: 'Marketing',
    component: () => import('../views/PlaceholderPage.vue'),
    meta: {
      title: '营销管理',
    },
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/PlaceholderPage.vue'),
    meta: {
      title: '系统设置',
    },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

export default router

