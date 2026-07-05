import { Suspense } from "react"
import { Sidebar } from "@/components/layout/sidebar"
import { AuthPrefetcher } from "@/lib/auth-prefetcher"

function SidebarFallback() {
  return (
    <aside className="flex h-screen w-56 flex-col border-r bg-card">
      <div className="flex h-14 items-center border-b px-4">
        <span className="text-lg font-bold tracking-tight">LinkForge</span>
      </div>
    </aside>
  )
}

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex">
      <AuthPrefetcher />
      <Suspense fallback={<SidebarFallback />}>
        <Sidebar />
      </Suspense>
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  )
}
