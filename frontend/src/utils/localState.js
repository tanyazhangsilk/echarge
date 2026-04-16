const clone = (value) => {
  if (typeof structuredClone === 'function') {
    return structuredClone(value)
  }
  return JSON.parse(JSON.stringify(value))
}

export const readLocalState = (key, fallbackValue) => {
  try {
    const raw = localStorage.getItem(key)
    if (!raw) {
      return clone(fallbackValue)
    }
    return JSON.parse(raw)
  } catch (error) {
    return clone(fallbackValue)
  }
}

export const writeLocalState = (key, value) => {
  localStorage.setItem(key, JSON.stringify(value))
  return value
}

export const upsertLocalItem = (key, item, fallbackList = [], matcher = (current) => current.id === item.id) => {
  const list = readLocalState(key, fallbackList)
  const index = list.findIndex((current) => matcher(current))
  if (index === -1) {
    list.unshift(item)
  } else {
    list.splice(index, 1, { ...list[index], ...item })
  }
  writeLocalState(key, list)
  return list
}
