"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import {
  LayoutDashboard, Link2, Plus, FolderOpen, Tags,
  Key, Webhook, Upload, Settings, Users, LogOut,
  Heart, History, Crown, Shield,
} from "lucide-react"
import { useAuthStore } from "@/store/auth"
import { auth } from "@/lib/api"

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/urls", label: "All URLs", icon: Link2 },
  { href: "/urls/new", label: "Create URL", icon: Plus },
  { href: "/favorites", label: "Favorites", icon: Heart },
  { href: "/workspaces", label: "Workspaces", icon: Users },
  { href: "/folders", label: "Folders", icon: FolderOpen },
  { href: "/tags", label: "Tags", icon: Tags },
  { href: "/api-keys", label: "API Keys", icon: Key },
  { href: "/webhooks", label: "Webhooks", icon: Webhook },
  { href: "/bulk", label: "Bulk Operations", icon: Upload },
  { href: "/audit-logs", label: "Audit Logs", icon: History },
  { href: "/billing", label: "Billing", icon: Crown },
  { href: "/profile", label: "Profile", icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()
  const { user, logout: storeLogout } = useAuthStore()

  const items = user?.is_superadmin
    ? [...navItems, { href: "/admin", label: "Admin", icon: Shield }]
    : navItems

  return (
    <aside className="flex h-screen w-56 flex-col border-r bg-card">
      <div className="flex h-14 items-center border-b px-4">
        <Link href="/dashboard" className="text-lg font-bold tracking-tight">LinkForge</Link>
      </div>
      <nav className="flex-1 space-y-1 p-3">
        {items.map((item) => {
          const Icon = item.icon
          const isActive = pathname === item.href || pathname.startsWith(item.href + "/")
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )}
            >
              <Icon className="size-4" />
              {item.label}
            </Link>
          )
        })}
      </nav>
      <div className="border-t p-3">
        <button
          onClick={() => { auth.logout().catch(() => {}); storeLogout(); window.location.href = "/login" }}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          <LogOut className="size-4" />
          Logout
        </button>
      </div>
    </aside>
  )
}
