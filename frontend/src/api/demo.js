import http from './http'

export const fetchDemoFlowHealth = () => http.get('/demo/flow/health')

export const startDemoOrder = (payload) => http.post('/demo/orders/start', payload)
export const finishDemoOrder = (orderId) => http.post(`/demo/orders/${orderId}/finish`)
export const markDemoOrderAbnormal = (orderId, payload) => http.post(`/demo/orders/${orderId}/abnormal`, payload)
export const fetchDemoOrderDetail = (orderId) => http.get(`/demo/orders/${orderId}`)

export const applyDemoStation = (payload) => http.post('/demo/stations/apply', payload)
export const approveDemoStation = (stationId, payload) => http.post(`/demo/stations/${stationId}/approve`, payload)
export const rejectDemoStation = (stationId, payload) => http.post(`/demo/stations/${stationId}/reject`, payload)
export const createDemoStationCharger = (stationId, payload) => http.post(`/demo/stations/${stationId}/chargers`, payload)
export const bindDemoStationTemplate = (stationId, payload) => http.post(`/demo/stations/${stationId}/bind-template`, payload)

export const runDemoSettlement = (payload) => http.post('/demo/settlements/run', payload)
export const fetchDemoSettlements = () => http.get('/demo/settlements')

export const applyDemoInvoice = (payload) => http.post('/demo/invoices/apply', payload)
export const processDemoInvoice = (invoiceId, payload) => http.post(`/demo/invoices/${invoiceId}/process`, payload)
export const fetchDemoInvoices = () => http.get('/demo/invoices')
