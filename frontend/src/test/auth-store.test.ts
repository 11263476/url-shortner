import { describe, it, expect, vi, beforeEach } from "vitest"
import { useAuthStore } from "@/store/auth"

describe("useAuthStore", () => {
  beforeEach(() => {
    useAuthStore.setState({ user: null, isLoading: true })
    localStorage.clear()
  })

  it("starts with no user", () => {
    const state = useAuthStore.getState()
    expect(state.user).toBeNull()
    expect(state.isLoading).toBe(true)
  })

  it("setUser updates user and stops loading", () => {
    const mockUser = {
      id: 1,
      email: "test@test.com",
      is_verified: true,
      role: "admin",
      plan: "premium",
      is_superadmin: false,
      avatar_url: null,
      created_at: "2024-01-01",
    }
    useAuthStore.getState().setUser(mockUser)
    const state = useAuthStore.getState()
    expect(state.user).toEqual(mockUser)
    expect(state.isLoading).toBe(false)
  })

  it("logout clears user and tokens", () => {
    localStorage.setItem("access_token", "test-token")
    localStorage.setItem("refresh_token", "test-refresh")
    useAuthStore.getState().logout()
    const state = useAuthStore.getState()
    expect(state.user).toBeNull()
    expect(localStorage.getItem("access_token")).toBeNull()
  })
})
