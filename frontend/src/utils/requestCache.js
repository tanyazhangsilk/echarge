import { getCurrentUserContext } from '../config/permissions'

export const DEFAULT_REQUEST_CACHE_TTL = 45 * 1000

const requestCache = new Map()

const isPlainObject = (value) => Object.prototype.toString.call(value) === '[object Object]'

const deepClone = (value) => {
  if (typeof structuredClone === 'function') {
    return structuredClone(value)
  }
  return JSON.parse(JSON.stringify(value))
}

const normalizeValue = (value) => {
  if (Array.isArray(value)) {
    return value.map(normalizeValue)
  }

  if (isPlainObject(value)) {
    return Object.keys(value)
      .sort()
      .reduce((result, key) => {
        const current = value[key]
        if (current === undefined || current === null || current === '') {
          return result
        }
        result[key] = normalizeValue(current)
        return result
      }, {})
  }

  return value
}

const serialize = (value) => JSON.stringify(normalizeValue(value))

export const buildRequestCacheKey = (url, params = {}, extra = {}) => {
  const { role, operatorId } = getCurrentUserContext()
  return serialize({
    url,
    params,
    role: extra.role || role,
    operatorId: extra.operatorId || operatorId,
    scope: extra.scope || '',
  })
}

export const getRequestCache = (key, { ttl = DEFAULT_REQUEST_CACHE_TTL, allowStale = true } = {}) => {
  const entry = requestCache.get(key)
  if (!entry) return null

  const age = Date.now() - entry.updatedAt
  const isFresh = age <= ttl

  if (!isFresh && !allowStale) {
    requestCache.delete(key)
    return null
  }

  return {
    value: deepClone(entry.value),
    updatedAt: entry.updatedAt,
    age,
    isFresh,
  }
}

export const setRequestCache = (key, value) => {
  requestCache.set(key, {
    value: deepClone(value),
    updatedAt: Date.now(),
  })
}

export const clearRequestCache = (matcher) => {
  if (!matcher) {
    requestCache.clear()
    return
  }

  for (const key of requestCache.keys()) {
    const matched = typeof matcher === 'function' ? matcher(key) : key.includes(String(matcher))
    if (matched) {
      requestCache.delete(key)
    }
  }
}

export const formatCacheUpdatedAt = (timestamp) => {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  })
}

export const formatCacheLabel = (timestamp, prefix = '最近更新于') => {
  const formatted = formatCacheUpdatedAt(timestamp)
  return formatted ? `${prefix} ${formatted}` : ''
}

export const shouldRefreshRequestCache = (key, ttl = DEFAULT_REQUEST_CACHE_TTL) => {
  const cached = getRequestCache(key, { ttl, allowStale: true })
  return !cached || !cached.isFresh
}
