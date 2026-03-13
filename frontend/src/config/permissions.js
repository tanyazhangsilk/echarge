import {
  Histogram,
  Tickets,
  Wallet,
  OfficeBuilding,
  DataAnalysis,
  Setting,
} from '@element-plus/icons-vue'

export const ROLE_DEFAULT_ROUTE = {
  admin: '/admin/dashboard',
  operator: '/operator/dashboard',
}

export const MODULES = {
  OVERVIEW: 'overview',
  ORDERS: 'orders',
  FINANCE_CARD: 'finance_card',
  FINANCE_SETTLEMENT: 'finance_settlement',
  FINANCE_INVOICE: 'finance_invoice',
  STATION_ASSET: 'station_asset',
  STATION_PRICING: 'station_pricing',
  STATION_REVIEW: 'station_review',
  SETTINGS: 'settings',
  BLUEPRINT: 'blueprint',
}

export const ROLE_PERMISSIONS = {
  admin: [
    MODULES.OVERVIEW,
    MODULES.ORDERS,
    MODULES.FINANCE_INVOICE,
    MODULES.STATION_REVIEW,
    MODULES.SETTINGS,
    MODULES.BLUEPRINT,
  ],
  operator: [
    MODULES.OVERVIEW,
    MODULES.ORDERS,
    MODULES.FINANCE_CARD,
    MODULES.FINANCE_SETTLEMENT,
    MODULES.STATION_ASSET,
    MODULES.STATION_PRICING,
    MODULES.SETTINGS,
    MODULES.BLUEPRINT,
  ],
}

const canAccess = (role, moduleCode) => ROLE_PERMISSIONS[role]?.includes(moduleCode)

export const hasModuleAccess = (role, moduleCode) => canAccess(role, moduleCode)

export const MENU_CONFIG = [
  {
    index: '/admin',
    icon: Histogram,
    title: '管理员中心',
    children: [
      { index: '/admin/dashboard', title: '管理员概览', moduleCode: MODULES.OVERVIEW },
      { index: '/admin/todo/stations', title: '电站审核', moduleCode: MODULES.STATION_REVIEW },
      { index: '/admin/todo/abnormal', title: '异常订单干预', moduleCode: MODULES.ORDERS },
      { index: '/admin/todo/invoice', title: '开票管理', moduleCode: MODULES.FINANCE_INVOICE },
    ],
  },
  {
    index: '/operator',
    icon: OfficeBuilding,
    title: '运营商中心',
    children: [
      { index: '/operator/dashboard', title: '运营概览', moduleCode: MODULES.OVERVIEW },
      { index: '/operator/assets/stations', title: '电站管理(建站)', moduleCode: MODULES.STATION_ASSET },
      { index: '/operator/assets/piles', title: '设备实时监控', moduleCode: MODULES.STATION_ASSET },
      { index: '/operator/pricing', title: '分时电价设置', moduleCode: MODULES.STATION_PRICING },
      { index: '/operator/orders/history', title: '历史订单', moduleCode: MODULES.ORDERS },
      { index: '/operator/orders/realtime', title: '实时订单', moduleCode: MODULES.ORDERS },
      { index: '/operator/finance/settlement', title: '收益对账', moduleCode: MODULES.FINANCE_SETTLEMENT },
      { index: '/operator/finance/cards', title: '资质与绑卡', moduleCode: MODULES.FINANCE_CARD },
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
