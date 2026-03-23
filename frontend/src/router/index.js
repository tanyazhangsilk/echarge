import { createRouter, createWebHistory } from 'vue-router'

import MainLayout from '../layouts/MainLayout.vue'
import PlaceholderPage from '../views/PlaceholderPage.vue'
import AdminDashboard from '../views/admin/AdminDashboard.vue'
import OperatorDashboard from '../views/operator/OperatorDashboard.vue'
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

const routes = [
  { path: '/', redirect: () => resolveRoleDefaultRoute(getStoredRole()) },
  {
    path: '/admin',
    component: MainLayout,
    meta: { role: ROLES.ADMIN },
    children: [
      { path: '', name: 'AdminDashboard', component: AdminDashboard, meta: { role: ROLES.ADMIN, title: '平台工作台', section: '总览' } },
      { path: 'institutions', name: 'AdminInstitutions', component: () => import('../views/admin/OperatorAudit.vue'), meta: { role: ROLES.ADMIN, title: '运营商审核', section: '审核中心' } },
      { path: 'institutions/stations', name: 'AdminInstitutionStations', component: () => import('../views/admin/todo/StationAudit.vue'), meta: { role: ROLES.ADMIN, title: '电站审核', section: '审核中心' } },
      { path: 'orders', name: 'AdminOrders', component: () => import('../views/orders/HistoryOrders.vue'), meta: { role: ROLES.ADMIN, title: '全局订单查询', section: '订单监管' } },
      { path: 'orders/anomalies', name: 'AdminOrderAnomalies', component: () => import('../views/orders/AbnormalOrders.vue'), meta: { role: ROLES.ADMIN, title: '异常订单监管', section: '订单监管' } },
      { path: 'finance', name: 'AdminFinance', component: () => import('../views/admin/GlobalSettle.vue'), meta: { role: ROLES.ADMIN, title: '清分结算执行', section: '资金清分' } },
      { path: 'finance/invoices', name: 'AdminFinanceInvoices', component: () => import('../views/finance/InvoiceManagement.vue'), meta: { role: ROLES.ADMIN, title: '发票合规抽查', section: '资金清分' } },
      { path: 'users', name: 'AdminUsers', component: () => import('../views/admin/UserManagement.vue'), meta: { role: ROLES.ADMIN, title: '用户列表', section: '用户管理' } },
      { path: 'users/blacklist', name: 'AdminUsersBlacklist', component: () => import('../views/admin/UserBlacklist.vue'), meta: { role: ROLES.ADMIN, title: '黑名单管理', section: '用户管理' } },
      { path: 'marketing', name: 'AdminMarketing', component: () => import('../views/admin/MarketingAudit.vue'), meta: { role: ROLES.ADMIN, title: '营销合规审计', section: '系统配置' } },
      { path: 'settings', name: 'AdminSettings', component: () => import('../views/RoleBlueprint.vue'), meta: { role: ROLES.ADMIN, title: '权限控制', section: '系统配置' } },
      { path: 'settings/params', name: 'AdminSettingsParams', component: () => import('../views/admin/SystemParams.vue'), meta: { role: ROLES.ADMIN, title: '系统参数设置', section: '系统配置' } },
    ],
  },
  {
    path: '/operator',
    component: MainLayout,
    meta: { role: ROLES.OPERATOR },
    children: [
      { path: '', name: 'OperatorDashboard', component: OperatorDashboard, meta: { role: ROLES.OPERATOR, title: '运营工作台', section: '总览' } },
      { path: 'stations', name: 'OperatorStations', component: () => import('../views/stations/StationList.vue'), meta: { role: ROLES.OPERATOR, title: '电站管理', section: '资产管理' } },
      { path: 'stations/chargers', name: 'OperatorStationsChargers', component: () => import('../views/stations/PileManagement.vue'), meta: { role: ROLES.OPERATOR, title: '设备状态总览', section: '资产管理' } },
      { path: 'billing', name: 'OperatorBilling', component: () => import('../views/stations/PricingSettings.vue'), meta: { role: ROLES.OPERATOR, title: '电价设置', section: '计费管理' } },
      { path: 'billing/templates', name: 'OperatorBillingTemplates', component: () => import('../views/operator/BillingTemplates.vue'), meta: { role: ROLES.OPERATOR, title: '电价模板管理', section: '计费管理' } },
      { path: 'orders', name: 'OperatorOrders', component: () => import('../views/orders/HistoryOrders.vue'), meta: { role: ROLES.OPERATOR, title: '历史订单', section: '订单管理' } },
      { path: 'orders/realtime', name: 'OperatorOrdersRealtime', component: () => import('../views/orders/RealtimeOrders.vue'), meta: { role: ROLES.OPERATOR, title: '实时订单监控', section: '订单管理' } },
      { path: 'finance', name: 'OperatorFinance', component: () => import('../views/finance/Settlement.vue'), meta: { role: ROLES.OPERATOR, title: '收益对账', section: '财务管理' } },
      { path: 'finance/bank-card', name: 'OperatorFinanceBankCard', component: () => import('../views/finance/CardManagement.vue'), meta: { role: ROLES.OPERATOR, title: '绑卡管理', section: '财务管理' } },
      { path: 'finance/invoices', name: 'OperatorFinanceInvoices', component: () => import('../views/finance/InvoiceManagement.vue'), meta: { role: ROLES.OPERATOR, title: '开票管理', section: '财务管理' } },
      { path: 'customers', name: 'OperatorCustomers', component: () => import('../views/operator/CustomerOverview.vue'), meta: { role: ROLES.OPERATOR, title: '车队与白名单', section: '客户管理' } },
      { path: 'customers/fleets', name: 'OperatorCustomerFleets', component: () => import('../views/operator/FleetManagement.vue'), meta: { role: ROLES.OPERATOR, title: '专属用户管理', section: '客户管理' } },
      { path: 'customers/tags', name: 'OperatorCustomerTags', component: () => import('../views/operator/TagManagement.vue'), meta: { role: ROLES.OPERATOR, title: '标签管理', section: '客户管理' } },
      { path: 'marketing', name: 'OperatorMarketing', component: () => import('../views/operator/MarketingDiscounts.vue'), meta: { role: ROLES.OPERATOR, title: '折扣优惠', section: '营销管理' } },
      { path: 'marketing/coupons', name: 'OperatorMarketingCoupons', component: () => import('../views/operator/CouponManagement.vue'), meta: { role: ROLES.OPERATOR, title: '优惠券发放', section: '营销管理' } },
      { path: 'settings', name: 'OperatorSettings', component: () => import('../views/operator/OperatorSettings.vue'), meta: { role: ROLES.OPERATOR, title: '系统设置', section: '系统' } },
    ],
  },
  { path: '/overview', redirect: () => roleAwareRedirect({ admin: '/admin', operator: '/operator' }) },
  { path: '/orders/history', redirect: () => roleAwareRedirect({ admin: '/admin/orders', operator: '/operator/orders' }) },
  { path: '/orders/realtime', redirect: () => roleAwareRedirect({ admin: '/admin/orders', operator: '/operator/orders/realtime' }) },
  { path: '/orders/abnormal', redirect: '/admin/orders/anomalies' },
  { path: '/finance/cards', redirect: '/operator/finance/bank-card' },
  { path: '/finance/settlement', redirect: '/operator/finance' },
  { path: '/finance/global-settle', redirect: '/admin/finance' },
  { path: '/finance/invoice', redirect: () => roleAwareRedirect({ admin: '/admin/finance/invoices', operator: '/operator/finance/invoices' }) },
  { path: '/stations/list', redirect: '/operator/stations' },
  { path: '/stations/piles', redirect: '/operator/stations/chargers' },
  { path: '/stations/pricing', redirect: '/operator/billing' },
  { path: '/stations/review', redirect: '/admin/institutions/stations' },
  { path: '/organizations/operators', redirect: '/admin/institutions' },
  { path: '/organizations/exclusive', redirect: '/operator/customers/fleets' },
  { path: '/users/fleet', redirect: '/operator/customers' },
  { path: '/users/whitelist', redirect: '/operator/customers' },
  { path: '/marketing/tags', redirect: '/operator/customers/tags' },
  { path: '/marketing/discounts', redirect: '/operator/marketing' },
  { path: '/role-blueprint', redirect: () => roleAwareRedirect({ admin: '/admin/settings', operator: '/operator/settings' }) },
  { path: '/settings', redirect: () => roleAwareRedirect({ admin: '/admin/settings', operator: '/operator/settings' }) },
  { path: '/legacy-placeholder', component: PlaceholderPage },
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
