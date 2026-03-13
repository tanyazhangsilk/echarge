import {
  Histogram,
  Tickets,
  Wallet,
  OfficeBuilding,
  UserFilled,
  Promotion,
  Setting,
  DataAnalysis,
} from '@element-plus/icons-vue'

export const ROLE_DEFAULT_ROUTE = {
  admin: '/role-blueprint',
  operator: '/overview',
}

export const MODULES = {
  OVERVIEW: 'overview',
  ORDERS: 'orders',
  FINANCE_CARD: 'finance_card',
  FINANCE_SETTLEMENT: 'finance_settlement',
  FINANCE_GLOBAL_SETTLE: 'finance_global_settle',
  FINANCE_INVOICE: 'finance_invoice',
  STATION_ASSET: 'station_asset',
  STATION_PRICING: 'station_pricing',
  STATION_REVIEW: 'station_review',
  ORG_OPERATOR_AUDIT: 'org_operator_audit',
  ORG_EXCLUSIVE: 'org_exclusive',
  USER_FLEET: 'user_fleet',
  USER_WHITELIST: 'user_whitelist',
  MARKETING: 'marketing',
  SETTINGS: 'settings',
  BLUEPRINT: 'blueprint',
}

export const ROLE_PERMISSIONS = {
  admin: [
    MODULES.OVERVIEW,
    MODULES.ORDERS,
    MODULES.FINANCE_INVOICE,
    MODULES.FINANCE_GLOBAL_SETTLE,
    MODULES.STATION_REVIEW,
    MODULES.ORG_OPERATOR_AUDIT,
    MODULES.ORG_EXCLUSIVE,
    MODULES.SETTINGS,
    MODULES.BLUEPRINT,
  ],
  operator: [
    MODULES.OVERVIEW,
    MODULES.ORDERS,
    MODULES.FINANCE_CARD,
    MODULES.FINANCE_SETTLEMENT,
    MODULES.FINANCE_INVOICE,
    MODULES.STATION_ASSET,
    MODULES.STATION_PRICING,
    MODULES.USER_FLEET,
    MODULES.USER_WHITELIST,
    MODULES.MARKETING,
    MODULES.SETTINGS,
    MODULES.BLUEPRINT,
  ],
}

const canAccess = (role, moduleCode) => ROLE_PERMISSIONS[role]?.includes(moduleCode)

export const hasModuleAccess = (role, moduleCode) => canAccess(role, moduleCode)

export const MENU_CONFIG = [
  { index: '/overview', icon: Histogram, title: '概览', moduleCode: MODULES.OVERVIEW },
  {
    index: '/orders',
    icon: Tickets,
    title: '订单管理',
    moduleCode: MODULES.ORDERS,
    children: [
      { index: '/orders/history', title: '历史订单', moduleCode: MODULES.ORDERS },
      { index: '/orders/realtime', title: '实时订单', moduleCode: MODULES.ORDERS },
      { index: '/orders/abnormal', title: '异常订单', moduleCode: MODULES.ORDERS },
    ],
  },
  {
    index: '/finance',
    icon: Wallet,
    title: '财务管理',
    children: [
      { index: '/finance/cards', title: '资质与绑卡', moduleCode: MODULES.FINANCE_CARD },
      { index: '/finance/settlement', title: '收益对账', moduleCode: MODULES.FINANCE_SETTLEMENT },
      { index: '/finance/global-settle', title: '平台清分执行', moduleCode: MODULES.FINANCE_GLOBAL_SETTLE },
      { index: '/finance/invoice', title: '开票管理', moduleCode: MODULES.FINANCE_INVOICE },
    ],
  },
  {
    index: '/stations',
    icon: OfficeBuilding,
    title: '电站电桩管理',
    children: [
      { index: '/stations/list', title: '电站列表', moduleCode: MODULES.STATION_ASSET },
      { index: '/stations/piles', title: '电桩管理', moduleCode: MODULES.STATION_ASSET },
      { index: '/stations/pricing', title: '电价设置', moduleCode: MODULES.STATION_PRICING },
      { index: '/stations/review', title: '电站审核', moduleCode: MODULES.STATION_REVIEW },
    ],
  },
  {
    index: '/organizations',
    icon: OfficeBuilding,
    title: '机构管理',
    children: [
      { index: '/organizations/operators', title: '运营商审核', moduleCode: MODULES.ORG_OPERATOR_AUDIT },
      { index: '/organizations/exclusive', title: '专属机构', moduleCode: MODULES.ORG_EXCLUSIVE },
    ],
  },
  {
    index: '/users',
    icon: UserFilled,
    title: '用户管理',
    children: [
      { index: '/users/fleet', title: '车队管理', moduleCode: MODULES.USER_FLEET },
      { index: '/users/whitelist', title: '白名单管理', moduleCode: MODULES.USER_WHITELIST },
    ],
  },
  {
    index: '/marketing',
    icon: Promotion,
    title: '营销管理',
    children: [
      { index: '/marketing/tags', title: '标签管理', moduleCode: MODULES.MARKETING },
      { index: '/marketing/discounts', title: '折扣活动', moduleCode: MODULES.MARKETING },
    ],
  },
  { index: '/role-blueprint', icon: DataAnalysis, title: '职责蓝图', moduleCode: MODULES.BLUEPRINT },
  { index: '/settings', icon: Setting, title: '系统设置', moduleCode: MODULES.SETTINGS },
]

export const buildMenuByRole = (role) => {
  const loop = (items) => {
    return items
      .map((item) => {
        if (item.children?.length) {
          const children = loop(item.children)
          return children.length ? { ...item, children } : null
        }

        if (!item.moduleCode || canAccess(role, item.moduleCode)) {
          return { ...item }
        }

        return null
      })
      .filter(Boolean)
  }

  return loop(MENU_CONFIG)
}
