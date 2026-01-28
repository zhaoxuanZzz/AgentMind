import { describe, it, expect, vi } from 'vitest'
import { debounce } from './debounce'

describe('debounce', () => {
  it('should debounce function calls', () => {
    vi.useFakeTimers()
    const func = vi.fn()
    const debouncedFunc = debounce(func, 1000)

    // Call it multiple times
    debouncedFunc()
    debouncedFunc()
    debouncedFunc()

    // Should not have been called yet
    expect(func).not.toHaveBeenCalled()

    // Fast forward time
    vi.advanceTimersByTime(1000)

    // Should have been called once
    expect(func).toHaveBeenCalledTimes(1)
    
    vi.useRealTimers()
  })
})
