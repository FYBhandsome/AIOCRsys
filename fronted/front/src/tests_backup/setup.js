import { vi } from 'vitest'
import axios from 'axios'
import MockAdapter from 'axios-mock-adapter'

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn()
  },
  ElLoading: {
    service: vi.fn(() => ({ close: vi.fn() }))
  }
}))

const originalLocalStorage = { ...global.localStorage }
global.localStorage = {
  getItem: vi.fn((key) => originalLocalStorage[key] || null),
  setItem: vi.fn((key, value) => { originalLocalStorage[key] = value }),
  removeItem: vi.fn((key) => { delete originalLocalStorage[key] }),
  clear: vi.fn(() => { Object.keys(originalLocalStorage).forEach(key => delete originalLocalStorage[key]) })
}

global.window = {
  location: {
    href: ''
  }
}

export function createMockAdapter(instance) {
  return new MockAdapter(instance)
}

export function resetMocks() {
  vi.clearAllMocks()
  localStorage.setItem.mockClear?.()
  localStorage.getItem.mockClear?.()
  localStorage.removeItem.mockClear?.()
  localStorage.clear.mockClear?.()
}

beforeEach(() => {
  resetMocks()
})
