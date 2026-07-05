import { create } from "zustand"
import { clearTokenCookies } from "@/lib/token-cookie"

export interface User {
  id: number
  email: string
  is_verified: boolean
  role: string
  plan: string
  is_superadmin: boolean
  avatar_url: string | null
  created_at: string
}

interface AuthState {
  user: User | null
  isLoading: boolean
  setUser: (user: User | null) => void
  setLoading: (loading: boolean) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  setUser: (user) => set({ user, isLoading: false }),
  setLoading: (isLoading) => set({ isLoading }),
  logout: () => {
    localStorage.removeItem("access_token")
    localStorage.removeItem("refresh_token")
    clearTokenCookies()
    set({ user: null })
  },
}))
