import { defineStore } from 'pinia'
import { ref } from 'vue'
import { mockOrders } from '../mock/orders'
import { ORDER_STATUS, PAY_STATUS, type Order, type OrderStats } from '../types/order'

const cloneOrders = (): Order[] => JSON.parse(JSON.stringify(mockOrders))

const safeNumber = (value: unknown): number => {
  const n = Number(value)
  return Number.isFinite(n) ? n : 0
}

const isToday = (dateStr: string | null): boolean => {
  if (!dateStr) return false
  const date = new Date(dateStr)
  if (Number.isNaN(date.getTime())) return false

  const now = new Date()
  return (
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate()
  )
}

export const useOrderStore = defineStore('order', () => {
  const orders = ref<Order[]>(cloneOrders())

  const getRealtimeOrders = (): Order[] =>
    orders.value
      .filter((order) => order.status === ORDER_STATUS.CHARGING)
      .sort((a, b) => new Date(b.startTime).getTime() - new Date(a.startTime).getTime())

  const getHistoryOrders = (): Order[] =>
    orders.value
      .filter((order) => order.status === ORDER_STATUS.COMPLETED)
      .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())

  const getAbnormalOrders = (): Order[] =>
    orders.value
      .filter((order) => order.status === ORDER_STATUS.ABNORMAL)
      .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())

  const getOrderById = (id: string): Order | undefined => orders.value.find((order) => order.id === id)

  const finishOrder = (id: string): Order | null => {
    const target = orders.value.find((order) => order.id === id)
    if (!target || target.status !== ORDER_STATUS.CHARGING) return null

    const now = new Date()
    const start = new Date(target.startTime)
    const diffMs = now.getTime() - start.getTime()
    const duration = Number.isFinite(diffMs) && diffMs > 0 ? Math.round(diffMs / 60000) : target.chargeDuration

    target.status = ORDER_STATUS.COMPLETED
    target.endTime = now.toISOString()
    target.chargeDuration = duration
    target.totalAmount = Number((safeNumber(target.electricityFee) + safeNumber(target.serviceFee)).toFixed(2))
    target.payStatus = PAY_STATUS.PAID
    target.updatedAt = now.toISOString()

    return target
  }

  const markOrderAbnormal = (id: string, reason: string): Order | null => {
    const target = orders.value.find((order) => order.id === id)
    if (!target || target.status !== ORDER_STATUS.CHARGING) return null

    target.status = ORDER_STATUS.ABNORMAL
    target.abnormalReason = reason?.trim() || '系统判定异常'
    target.updatedAt = new Date().toISOString()

    return target
  }

  const getOrderStats = (): OrderStats => {
    const chargingCount = orders.value.filter((order) => order.status === ORDER_STATUS.CHARGING).length
    const todayCompleted = orders.value.filter(
      (order) => order.status === ORDER_STATUS.COMPLETED && isToday(order.endTime || order.updatedAt),
    )
    const abnormalCount = orders.value.filter((order) => order.status === ORDER_STATUS.ABNORMAL).length

    return {
      chargingCount,
      todayCompletedCount: todayCompleted.length,
      todayTotalChargeAmount: Number(todayCompleted.reduce((sum, item) => sum + safeNumber(item.chargeAmount), 0).toFixed(2)),
      todayTotalAmount: Number(todayCompleted.reduce((sum, item) => sum + safeNumber(item.totalAmount), 0).toFixed(2)),
      abnormalCount,
    }
  }

  return {
    orders,
    getRealtimeOrders,
    getHistoryOrders,
    getAbnormalOrders,
    getOrderById,
    finishOrder,
    markOrderAbnormal,
    getOrderStats,
  }
})
