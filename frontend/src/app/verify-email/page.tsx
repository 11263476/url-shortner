"use client"

import { useEffect, useState, Suspense } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { auth, getErrorMessage } from "@/lib/api"
import { CheckCircle, XCircle } from "lucide-react"

function VerifyEmailInner() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const token = searchParams.get("token")
  const [status, setStatus] = useState<"loading" | "success" | "error">(
    token ? "loading" : "error",
  )
  const [message, setMessage] = useState(token ? "" : "No verification token provided.")

  useEffect(() => {
    if (!token) return
    auth.verifyEmail(token)
      .then(() => {
        setStatus("success")
        setMessage("Email verified successfully! You can now close this page.")
        setTimeout(() => router.push("/login"), 3000)
      })
      .catch((err: unknown) => {
        setStatus("error")
        setMessage(getErrorMessage(err, "Verification failed."))
      })
  }, [router, token])

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-950 p-6">
      <Card className="w-full max-w-md">
        <CardHeader>
          <div className="flex items-center justify-center mb-4">
            {status === "loading" ? (
              <div className="size-12 animate-spin rounded-full border-4 border-blue-400 border-t-transparent" />
            ) : status === "success" ? (
              <CheckCircle className="size-12 text-green-400" />
            ) : (
              <XCircle className="size-12 text-red-400" />
            )}
          </div>
          <CardTitle className="text-center">
            {status === "loading" ? "Verifying..." : status === "success" ? "Verified!" : "Verification Failed"}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-center text-sm text-muted-foreground">{message}</p>
        </CardContent>
      </Card>
    </div>
  )
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center bg-zinc-950">
        <div className="size-12 animate-spin rounded-full border-4 border-blue-400 border-t-transparent" />
      </div>
    }>
      <VerifyEmailInner />
    </Suspense>
  )
}
