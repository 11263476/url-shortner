"use client"

import { Suspense, useState } from "react"

import Link from "next/link"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { Button } from "@/components/ui/button"
import { BackgroundBeams } from "@/components/ui/background-beams"
import { auth, getErrorMessage } from "@/lib/api"
import { registerSchema, type RegisterFormData } from "@/lib/schemas"

function RegisterForm() {
  const [success, setSuccess] = useState(false)

  const { register, handleSubmit, setError, formState: { errors, isSubmitting } } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  })

  async function onSubmit(data: RegisterFormData) {
    try {
      await auth.register(data.email, data.password)
      setSuccess(true)
    } catch (err: unknown) {
      setError("root", { message: getErrorMessage(err, "Registration failed") })
    }
  }

  if (success) {
    return (
      <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-zinc-950 px-4">
        <BackgroundBeams className="opacity-50" />
        <div className="relative z-10 w-full max-w-sm rounded-xl border border-zinc-800 bg-zinc-900/80 p-8 shadow-2xl backdrop-blur-sm text-center">
          <h1 className="text-2xl font-bold text-white mb-4">Account Created</h1>
          <p className="text-zinc-400 mb-6">Check your email to verify your account, then sign in.</p>
          <Link href="/login" className="inline-block rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">Sign In</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-zinc-950 px-4">
      <BackgroundBeams className="opacity-50" />
      <div className="relative z-10 w-full max-w-sm">
        <form onSubmit={handleSubmit(onSubmit)} className="mb-4 space-y-4 rounded-xl border border-zinc-800 bg-zinc-900/80 p-8 shadow-2xl backdrop-blur-sm">
          <h1 className="text-center text-2xl font-bold text-white">Create Account</h1>

          {errors.root && <p className="text-center text-sm text-red-400">{errors.root.message}</p>}

          <div>
            <input
              type="email"
              placeholder="Email"
              {...register("email")}
              className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.email && <p className="mt-1 text-xs text-red-400">{errors.email.message}</p>}
          </div>

          <div>
            <input
              type="password"
              placeholder="Password"
              {...register("password")}
              className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.password && <p className="mt-1 text-xs text-red-400">{errors.password.message}</p>}
          </div>

          <div>
            <input
              type="password"
              placeholder="Confirm Password"
              {...register("confirmPassword")}
              className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.confirmPassword && <p className="mt-1 text-xs text-red-400">{errors.confirmPassword.message}</p>}
          </div>

          <Button type="submit" className="w-full bg-blue-600 text-white hover:bg-blue-700" disabled={isSubmitting}>
            {isSubmitting ? "Creating account..." : "Create Account"}
          </Button>

          <p className="text-center text-sm text-zinc-400">
            Already have an account?{" "}
            <Link href="/login" className="text-blue-400 hover:underline">Sign In</Link>
          </p>
        </form>
      </div>
    </div>
  )
}

export default function RegisterPage() {
  return <Suspense fallback={<div className="flex min-h-screen items-center justify-center bg-zinc-950 text-white">Loading...</div>}><RegisterForm /></Suspense>
}
