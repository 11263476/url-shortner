import { Suspense } from "react"
import { Sidebar } from "@/components/layout/sidebar"
import { AuthPrefetcher } from "@/lib/auth-prefetcher"

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <AuthPrefetcher />
      <Suspense fallback={null}>
        <Sidebar />
      </Suspense>
      <main className="relative flex-1 overflow-auto pt-14 md:pt-0">
        <div className="pointer-events-none fixed right-0 top-0 h-96 w-96 -translate-y-1/2 translate-x-1/2 rounded-full bg-blue-500/5 blur-[128px]" />
        <div className="pointer-events-none fixed bottom-0 left-1/2 h-64 w-64 -translate-x-1/2 rounded-full bg-purple-500/5 blur-[96px]" />
        {children}
      </main>
    </div>
  )
}
