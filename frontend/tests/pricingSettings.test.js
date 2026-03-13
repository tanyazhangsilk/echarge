import { mount } from '@vue/test-utils'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import ElementPlus from 'element-plus'

import PricingSettings from '../src/views/stations/PricingSettings.vue'

vi.mock('sortablejs', () => ({
  default: {
    create: () => ({ destroy: () => {} }),
  },
}))

vi.mock('element-plus', async () => {
  const actual = await vi.importActual('element-plus')
  return {
    ...actual,
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
      info: vi.fn(),
      warning: vi.fn(),
    },
  }
})

describe('PricingSettings', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('opens apply dialog and applies selected stations', async () => {
    const wrapper = mount(PricingSettings, { global: { plugins: [ElementPlus] } })
    const vm = wrapper.vm

    vm.openApplyDialog()
    expect(vm.applyDialogVisible).toBe(true)

    vm.handleStationSelectionChange([{ id: 'st-001', name: '南山科技园充电站' }])
    await vm.confirmApplyStations()

    expect(vm.currentTemplate.stationIds).toEqual(['st-001'])
  })
})
