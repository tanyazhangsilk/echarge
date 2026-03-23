import {
  Histogram,
  Tickets,
  Wallet,
  OfficeBuilding,
  UserFilled,
  Promotion,
  Setting,
  DataAnalysis,
  CreditCard,
  Document,
  Bell,
  Connection,
} from '@element-plus/icons-vue'

export const ROLES = {
  ADMIN: 'admin',
  OPERATOR: 'operator',
}

export const ROLE_LABELS = {
  [ROLES.ADMIN]: '平台管理员',
  [ROLES.OPERATOR]: '运营商',
}

export const ROLE_DEFAULT_ROUTE = {
  [ROLES.ADMIN]: '/admin',
  [ROLES.OPERATOR]: '/operator',
}

export const getStoredRole = () => {
  const saved = localStorage.getItem('userRole')
  return saved === ROLES.ADMIN ? ROLES.ADMIN : ROLES.OPERATOR
}

export const setStoredRole = (role) => {
  localStorage.setItem('userRole', role === ROLES.ADMIN ? ROLES.ADMIN : ROLES.OPERATOR)
}

export const resolveRoleDefaultRoute = (role) => ROLE_DEFAULT_ROUTE[role] || ROLE_DEFAULT_ROUTE[ROLES.OPERATOR]

export const getRoleByPath = (path = '') => {
  if (path.startsWith('/admin')) return ROLES.ADMIN
  if (path.startsWith('/operator')) return ROLES.OPERATOR
  return null
}

export const MENU_CONFIG = {
  [ROLES.ADMIN]: [
    {
      label: '概览',
      items: [{ index: '/admin', title: '工作台', icon: Histogram }],
    },
    {
      label: '机构管理',
      items: [
        { index: '/admin/institutions', title: '运营商入驻审核', icon: OfficeBuilding },
        { index: '/admin/institutions/stations', title: '电站上架审批', icon: Bell },
      ],
    },
    {
      label: '订单监管',
      items: [
        { index: '/admin/orders', title: '全局订单查询', icon: Tickets },
        { index: '/admin/orders/anomalies', title: '异常订单监管', icon: Connection },
      ],
    },
    {
      label: '资金清分',
      items: [
        { index: '/admin/finance', title: '清分结算执行', icon: Wallet },
        { index: '/admin/finance/invoices', title: '发票合规抽查', icon: Document },
      ],
    },
    {
      label: '用户管理',
      items: [
        { index: '/admin/users', title: '用户列表', icon: UserFilled },
        { index: '/admin/users/blacklist', title: '封禁用户管理', icon: UserFilled },
      ],
    },
    {
      label: '系统配置',
      items: [
        { index: '/admin/marketing', title: '营销合规审计', icon: Promotion },
        { index: '/admin/settings', title: '权限控制', icon: DataAnalysis },
        { index: '/admin/settings/params', title: '系统参数设置', icon: Setting },
      ],
    },
  ],
  [ROLES.OPERATOR]: [
    {
      label: '概览',
      items: [{ index: '/operator', title: '工作台', icon: Histogram }],
    },
    {
      label: '资产管理',
      items: [
        { index: '/operator/stations', title: '站点管理', icon: OfficeBuilding },
        { index: '/operator/stations/chargers', title: '设备状态总览', icon: Connection },
      ],
    },
    {
      label: '计费管理',
      items: [
        { index: '/operator/billing', title: '电价设置', icon: DataAnalysis },
        { index: '/operator/billing/templates', title: '计费模板管理', icon: Document },
      ],
    },
    {
      label: '订单管理',
      items: [
        { index: '/operator/orders', title: '历史订单', icon: Tickets },
        { index: '/operator/orders/realtime', title: '实时订单监控', icon: Bell },
      ],
    },
    {
      label: '财务管理',
      items: [
        { index: '/operator/finance', title: '收益对账', icon: Wallet },
        { index: '/operator/finance/bank-card', title: '绑卡管理', icon: CreditCard },
        { index: '/operator/finance/invoices', title: '开票管理', icon: Document },
      ],
    },
    {
      label: '客户管理',
      items: [
        { index: '/operator/customers', title: '车队与白名单', icon: UserFilled },
        { index: '/operator/customers/fleets', title: '专属用户管理', icon: UserFilled },
        { index: '/operator/customers/tags', title: '标签管理', icon: Promotion },
      ],
    },
    {
      label: '营销管理',
      items: [
        { index: '/operator/marketing', title: '折扣优惠', icon: Promotion },
        { index: '/operator/marketing/coupons', title: '优惠券发放', icon: Promotion },
      ],
    },
    {
      label: '系统',
      items: [{ index: '/operator/settings', title: '系统设置', icon: Setting }],
    },
  ],
}

export const buildMenuByRole = (role) => MENU_CONFIG[role] || MENU_CONFIG[ROLES.OPERATOR]
