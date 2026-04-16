import http from './http'

export const fetchBillingTemplates = () => http.get('/operator/billing/templates')
export const createBillingTemplate = (payload) => http.post('/operator/billing/templates', payload)
export const updateBillingTemplate = (id, payload) => http.put(`/operator/billing/templates/${id}`, payload)

export const fetchCustomerOverview = () => http.get('/operator/customers/overview')
export const fetchFleets = () => http.get('/operator/customers/fleets')
export const createFleet = (payload) => http.post('/operator/customers/fleets', payload)
export const fetchTags = () => http.get('/operator/customers/tags')
export const createTag = (payload) => http.post('/operator/customers/tags', payload)

export const fetchDiscounts = () => http.get('/operator/marketing/discounts')
export const createDiscount = (payload) => http.post('/operator/marketing/discounts', payload)
export const fetchCoupons = () => http.get('/operator/marketing/coupons')
export const createCoupon = (payload) => http.post('/operator/marketing/coupons', payload)
export const dispatchCoupon = (id, payload) => http.post(`/operator/marketing/coupons/${id}/dispatch`, payload)

export const fetchOperatorProfile = () => http.get('/operator/settings/profile')
export const updateOperatorProfile = (payload) => http.put('/operator/settings/profile', payload)

export const fetchOperatorStations = (params = {}) => http.get('/operator/stations', { params })
export const fetchOperatorStationOptions = (params = {}) => http.get('/operator/stations/options', { params })
export const fetchStationChargers = (stationId) => http.get(`/operator/stations/${stationId}/chargers`)
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
export const startDemoCharging = (payload = {}) => http.post('/operator/orders/demo-start', payload)
export const finishOperatorOrder = (orderId) => http.post(`/operator/orders/${orderId}/finish`)
export const forceStopOperatorOrder = (orderId) => http.post(`/operator/orders/${orderId}/force-stop`)
export const markOperatorOrderAbnormal = (orderId, abnormalReason) =>
  http.post(`/operator/orders/${orderId}/mark-abnormal`, { abnormal_reason: abnormalReason })
