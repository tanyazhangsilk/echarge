import http from './http'

export const fetchOperatorAudits = () => http.get('/admin/operators/audits')
export const processOperatorAudit = (id, payload) => http.post(`/admin/operators/${id}/process`, payload)

export const fetchAdminUsers = () => http.get('/admin/users')
export const toggleAdminUserBlacklist = (id) => http.post(`/admin/users/${id}/toggle-blacklist`)
export const fetchAdminBlacklist = () => http.get('/admin/users/blacklist')

export const fetchMarketingAudits = () => http.get('/admin/marketing/audits')
export const processMarketingAudit = (id, payload) => http.post(`/admin/marketing/audits/${id}/process`, payload)

export const fetchSystemParams = () => http.get('/admin/settings/params')
export const updateSystemParams = (payload) => http.put('/admin/settings/params', payload)
export const fetchAdminPermissionSettings = () => http.get('/admin/settings/permissions')
export const updateAdminPermissionSettings = (payload) => http.put('/admin/settings/permissions', payload)

export const fetchStationAudits = () => http.get('/admin/audit/stations')
export const processStationAudit = (stationId, payload) => http.post(`/admin/audit/stations/${stationId}/process`, payload)
export const fetchAdminStationOptions = (params = {}) => http.get('/admin/stations/options', { params })

export const fetchAdminOrders = (params = {}) => http.get('/admin/orders', { params })
export const fetchAdminAbnormalOrders = (params = {}) => http.get('/admin/orders/abnormal', { params })
export const fetchAdminOrderDetail = (orderId) => http.get(`/admin/orders/${orderId}`)
