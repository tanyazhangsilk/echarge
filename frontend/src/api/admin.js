import http from './http'
import { mockAdminUsers, mockBlacklistRows, mockMarketingAudits } from '../mock/backoffice'

const clone = (value) => JSON.parse(JSON.stringify(value))
const resolveMock = (data, extra = {}) => Promise.resolve({ data: { data: clone(data), ...clone(extra) } })

let adminUsersState = clone(mockAdminUsers.rows)
let blacklistState = clone(mockBlacklistRows)
let marketingAuditsState = clone(mockMarketingAudits)

const getAdminUserSummary = () => ({
  total_users: adminUsersState.length,
  active_users: adminUsersState.filter((item) => item.status !== 'blacklisted').length,
  blacklisted_users: adminUsersState.filter((item) => item.status === 'blacklisted').length,
})

export const fetchOperatorAudits = () => http.get('/admin/operators/audits')
export const processOperatorAudit = (id, payload) => http.post(`/admin/operators/${id}/process`, payload)
export const processOperatorBankCard = (id, payload) => http.post(`/admin/operators/${id}/bank-card/process`, payload)

export const fetchAdminUsers = () => resolveMock(adminUsersState, { summary: getAdminUserSummary() })
export const toggleAdminUserBlacklist = (id) => {
  const target = adminUsersState.find((item) => Number(item.id) === Number(id))
  if (target) {
    const nextBlacklisted = target.status !== 'blacklisted'
    target.status = nextBlacklisted ? 'blacklisted' : 'active'

    if (nextBlacklisted) {
      if (!blacklistState.some((item) => Number(item.id) === Number(id))) {
        blacklistState.unshift({
          id: target.id,
          name: target.name,
          phone: target.phone,
          reason: '运营风控演示名单',
          created_at: new Date().toLocaleString('zh-CN', { hour12: false }),
        })
      }
    } else {
      blacklistState = blacklistState.filter((item) => Number(item.id) !== Number(id))
    }
  }

  return Promise.resolve({ data: { message: 'ok' } })
}
export const fetchAdminBlacklist = () => resolveMock(blacklistState)

export const fetchMarketingAudits = () => resolveMock(marketingAuditsState)
export const processMarketingAudit = (id, payload) => {
  const target = marketingAuditsState.find((item) => Number(item.id) === Number(id))
  if (target) {
    const isApproved = payload?.action === 'approve'
    target.audit_status = isApproved ? 'approved' : 'rejected'
    target.remark = payload?.remark || (isApproved ? '审核通过' : '已驳回')
  }
  return Promise.resolve({ data: { message: 'ok' } })
}

export const fetchSystemParams = () => http.get('/admin/settings/params')
export const updateSystemParams = (payload) => http.put('/admin/settings/params', payload)
export const fetchAdminPermissionSettings = () => http.get('/admin/settings/permissions')
export const updateAdminPermissionSettings = (payload) => http.put('/admin/settings/permissions', payload)

export const fetchStationAudits = (params = {}) => http.get('/admin/audit/stations', { params })
export const processStationAudit = (stationId, payload) => http.post(`/admin/audit/stations/${stationId}/process`, payload)
export const fetchAdminStationOptions = (params = {}) => http.get('/admin/stations/options', { params })

export const fetchAdminOrders = (params = {}) => http.get('/admin/orders', { params })
export const fetchAdminAbnormalOrders = (params = {}) => http.get('/admin/orders/abnormal', { params })
export const fetchAdminOrderDetail = (orderId) => http.get(`/admin/orders/${orderId}`)
