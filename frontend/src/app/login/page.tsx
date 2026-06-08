"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { auth, workspaces } from "@/lib/api"
import { useAuthStore } from "@/store/auth"

export default function LoginPage() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [isRegister, setIsRegister] = useState(false)
  const router = useRouter()
  const setUser = useAuthStore((s) => s.setUser)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError("")
    try {
      if (isRegister) {
        await auth.register(email, password)
      }
      const tokens = await auth.login(email, password)
      localStorage.setItem("access_token", tokens.access_token)
      localStorage.setItem("refresh_token", tokens.refresh_token)
      const user = await auth.me()
      setUser(user)
      router.push("/dashboard")
    } catch (err: any) {
      setError(err.message)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 px-4">
      <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-4 rounded-xl bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-bold text-center">{isRegister ? "Create Account" : "Sign In"}</h1>
        {error && <p className="text-sm text-red-600 text-center">{error}</p>}
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="w-full rounded-lg border px-3 py-2 text-sm"
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          className="w-full rounded-lg border px-3 py-2 text-sm"
        />
        <Button type="submit" className="w-full">
          {isRegister ? "Register" : "Sign In"}
        </Button>
        <p className="text-center text-sm text-zinc-500">
          {isRegister ? "Already have an account?" : "No account?"}{" "}
          <button type="button" onClick={() => setIsRegister(!isRegister)} className="text-blue-600 hover:underline">
            {isRegister ? "Sign in" : "Register"}
          </button>
        </p>
      </form>
    </div>
  )
}
