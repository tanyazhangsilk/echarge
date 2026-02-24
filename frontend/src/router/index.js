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
    component: () => import('../views/PlaceholderPage.vue'),
    meta: {
      title: '订单管理',
    },
  },
  {
    path: '/finance',
    name: 'Finance',
    component: () => import('../views/PlaceholderPage.vue'),
    meta: {
      title: '财务管理',
    },
  },
  {
    path: '/stations',
    name: 'Stations',
    component: () => import('../views/PlaceholderPage.vue'),
    meta: {
      title: '电站电桩管理',
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

