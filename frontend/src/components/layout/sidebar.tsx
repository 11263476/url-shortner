"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import {
  LayoutDashboard, Link2, Plus, FolderOpen, Tags,
  Key, Webhook, Upload, Settings, Users, LogOut,
  Heart, History, Crown, Shield, Menu, X,
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
  const [open, setOpen] = useState(false)
  const pathname = usePathname()
  const { user, logout: storeLogout } = useAuthStore()

  const items = user?.is_superadmin
    ? [...navItems, { href: "/admin", label: "Admin", icon: Shield }]
    : navItems

  const content = (
    <>
      <div className="flex h-14 items-center justify-between border-b bg-gradient-to-r from-blue-600/5 to-purple-600/5 px-4">
        <Link href="/dashboard" className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-lg font-bold text-transparent">LinkForge</Link>
        <button onClick={() => setOpen(false)} className="block md:hidden p-1 text-muted-foreground hover:text-foreground">
          <X className="size-5" />
        </button>
      </div>
      <nav className="flex-1 space-y-1 overflow-y-auto p-3">
        {items.map((item) => {
          const Icon = item.icon
          const isActive = pathname === item.href || pathname.startsWith(item.href + "/")
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setOpen(false)}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all",
                isActive
                  ? "bg-blue-500/10 text-blue-400 border-l-2 border-blue-500 -ml-px"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50 border-l-2 border-transparent",
              )}
            >
              <Icon className="size-4 shrink-0" />
              {item.label}
            </Link>
          )
        })}
      </nav>
      <div className="border-t border-zinc-800 p-3">
        <button
          onClick={() => { auth.logout().catch(() => {}); storeLogout(); window.location.href = "/login" }}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-zinc-400 transition-colors hover:text-zinc-200 hover:bg-zinc-800/50"
        >
          <LogOut className="size-4 shrink-0" />
          Logout
        </button>
      </div>
    </>
  )

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="fixed left-3 top-3 z-40 block md:hidden rounded-lg bg-card p-2 shadow-lg border"
        aria-label="Open menu"
      >
        <Menu className="size-5" />
      </button>

      {open && (
        <div
          className="fixed inset-0 z-30 bg-black/50 md:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      <aside
        className={cn(
          "flex h-screen w-56 flex-col border-r border-zinc-800 bg-zinc-950 fixed md:sticky top-0 left-0 z-40 transition-transform duration-200 md:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        {content}
      </aside>
    </>
  )
}
