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
