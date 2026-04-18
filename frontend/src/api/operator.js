import http from './http'
import {
  mockCoupons,
  mockCustomerOverview,
  mockDiscounts,
  mockFleets,
  mockOperatorProfile,
  mockOperatorSettingContacts,
  mockTags,
} from '../mock/backoffice'

const clone = (value) => JSON.parse(JSON.stringify(value))
const resolveMock = (data, extra = {}) => Promise.resolve({ data: { data: clone(data), ...clone(extra) } })

let fleetState = clone(mockFleets)
let tagState = clone(mockTags)
let discountState = clone(mockDiscounts)
let couponState = clone(mockCoupons)
let operatorProfileState = clone(mockOperatorProfile)
let operatorContactsState = clone(mockOperatorSettingContacts)
const customerOverviewState = clone(mockCustomerOverview)

const getCustomerOverviewPayload = () => ({
  summary: {
    fleet_count: fleetState.length,
    whitelist_count: fleetState.filter((item) => item.is_whitelist).length,
    member_count: customerOverviewState.members.length,
  },
  members: customerOverviewState.members,
})

export const fetchBillingTemplates = () => http.get('/operator/billing/templates')
export const createBillingTemplate = (payload) => http.post('/operator/billing/templates', payload)
export const updateBillingTemplate = (id, payload) => http.put(`/operator/billing/templates/${id}`, payload)

export const fetchCustomerOverview = () => resolveMock(getCustomerOverviewPayload())
export const fetchFleets = () => resolveMock(fleetState)
export const createFleet = (payload) => {
  fleetState.unshift({
    id: Date.now(),
    name: payload?.name?.trim() || '未命名车队',
    member_count: 0,
    is_whitelist: Boolean(payload?.is_whitelist),
    created_at: new Date().toLocaleString('zh-CN', { hour12: false }),
  })
  return Promise.resolve({ data: { message: 'ok' } })
}
export const fetchTags = () => resolveMock(tagState)
export const createTag = (payload) => {
  tagState.unshift({
    id: Date.now(),
    name: payload?.name?.trim() || '新标签',
    color: payload?.color || '#409EFF',
    description: payload?.description || '',
    user_count: 0,
  })
  return Promise.resolve({ data: { message: 'ok' } })
}

export const fetchDiscounts = () => resolveMock(discountState)
export const createDiscount = (payload) => {
  discountState.unshift({
    id: Date.now(),
    name: payload?.name?.trim() || '新活动',
    campaign_type: payload?.campaign_type || '满减',
    discount_value: String(payload?.discount_value ?? 0),
    threshold: payload?.threshold ? `满${payload.threshold} 可用` : '不限门槛',
    audience: payload?.audience || '运营用户',
    redeem_count: 0,
    conversion_rate: '0%',
    status: payload?.status || '待审核',
  })
  return Promise.resolve({ data: { message: 'ok' } })
}
export const fetchCoupons = () => resolveMock(couponState)
export const createCoupon = (payload) => {
  couponState.unshift({
    id: Date.now(),
    name: payload?.name?.trim() || '新优惠券',
    discount_value: `${payload?.discount_value ?? 0} 元`,
    inventory: Number(payload?.inventory || 0),
    dispatched: 0,
    used: 0,
    status: payload?.status || '待投放',
  })
  return Promise.resolve({ data: { message: 'ok' } })
}
export const dispatchCoupon = (id, payload) => {
  const target = couponState.find((item) => Number(item.id) === Number(id))
  if (target) {
    target.dispatched = Number(target.dispatched || 0) + Number(payload?.dispatch_count || 0)
    target.status = '投放中'
  }
  return Promise.resolve({ data: { message: 'ok' } })
}

export const fetchOperatorProfile = () =>
  resolveMock({
    ...operatorProfileState,
    contact_matrix: operatorContactsState,
  })
export const updateOperatorProfile = (payload) => {
  operatorProfileState = {
    ...operatorProfileState,
    ...payload,
  }
  return Promise.resolve({ data: { message: 'ok' } })
}

export const fetchOperatorStations = (params = {}) => http.get('/operator/stations', { params })
export const fetchOperatorStationOptions = (params = {}) => http.get('/operator/stations/options', { params })
export const fetchStationChargers = (stationId) => http.get(`/operator/stations/${stationId}/chargers`)
export const createStationCharger = (stationId, payload) => http.post(`/operator/stations/${stationId}/chargers`, payload)
export const batchCreateStationChargers = (stationId, payload) =>
  http.post(`/operator/stations/${stationId}/chargers/batch-create`, payload)
export const updateStationCharger = (stationId, chargerId, payload) =>
  http.patch(`/operator/stations/${stationId}/chargers/${chargerId}`, payload)
export const updateStationVisibility = (stationId, visibility) =>
  http.post(`/operator/stations/${stationId}/visibility`, { visibility })
export const bindStationTemplate = (stationId, templateId) =>
  http.post(`/operator/stations/${stationId}/bind-template`, { template_id: templateId })
export const fetchOperatorPricingTemplates = () => http.get('/operator/pricing/templates')
export const applyOperatorStation = (payload) => http.post('/operator/stations/apply', payload)

export const fetchOperatorRealtimeOrders = (params = {}) => http.get('/operator/orders/realtime', { params })
export const fetchOperatorHistoryOrders = (params = {}) => http.get('/operator/orders/history', { params })
export const fetchOperatorAbnormalOrders = (params = {}) => http.get('/operator/orders/abnormal', { params })
export const fetchOperatorOrderDetail = (orderId) => http.get(`/operator/orders/${orderId}`)
export const fetchOperatorOrderStartOptions = (params = {}) => http.get('/operator/orders/start-options', { params })
export const startDemoCharging = (payload = {}) => http.post('/operator/orders/demo-start', payload)
export const finishOperatorOrder = (orderId) => http.post(`/operator/orders/${orderId}/finish`)
export const forceStopOperatorOrder = (orderId) => http.post(`/operator/orders/${orderId}/force-stop`)
export const markOperatorOrderAbnormal = (orderId, abnormalReason) =>
  http.post(`/operator/orders/${orderId}/mark-abnormal`, { abnormal_reason: abnormalReason })
