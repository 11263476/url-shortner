"use client"

import { useEffect } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { StatsCardSkeleton, TableSkeleton } from "@/components/ui/skeleton"
import { useDashboard } from "@/hooks/useDashboard"
import { BarChart3, ExternalLink, Plus, Link2, Activity, Crown, AlertTriangle, MousePointerClick } from "lucide-react"

export default function DashboardPage() {
  useEffect(() => { document.title = "Dashboard - LinkForge" }, [])

  const {
    urlList, totalUrlsCount, workspaces, wsId, error, quota,
    canEdit, activeUrls, isLoading,
    setWsId,
  } = useDashboard()

  const stats = [
    { title: "Total URLs", value: totalUrlsCount, icon: Link2, gradient: "from-blue-500 to-cyan-500" },
    { title: "Active", value: activeUrls.length, icon: Activity, gradient: "from-green-500 to-emerald-500" },
    { title: "Plan", value: "free", icon: Crown, gradient: "from-purple-500 to-pink-500" },
  ]

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="mb-6 h-8 w-48 animate-pulse rounded bg-zinc-800/50" />
        <StatsCardSkeleton />
        <div className="mt-6"><TableSkeleton rows={4} /></div>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-bold">Dashboard</h1>
            <Select value={String(wsId ?? "")} onChange={(e) => setWsId(e.target.value ? Number(e.target.value) : null)} className="w-44">
              <option value="">All workspaces</option>
              {workspaces.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
            </Select>
          </div>
        </div>
        {canEdit && (
          <Link href="/urls/new">
            <Button className="bg-blue-600 text-white hover:bg-blue-700">
              <Plus className="mr-1 size-4" />Create URL
            </Button>
          </Link>
        )}
      </div>

      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        {stats.map((s) => {
          const Icon = s.icon
          return (
            <Card key={s.title} className="relative overflow-hidden">
              <div className={`absolute inset-0 bg-gradient-to-br ${s.gradient} opacity-5`} />
              <CardContent className="relative flex items-center gap-4 pt-6">
                <div className={`rounded-xl bg-gradient-to-br ${s.gradient} p-3 shadow-lg`}>
                  <Icon className="size-6 text-white" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{s.title}</p>
                  <p className="text-2xl font-bold">{s.value}</p>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <div className="mb-6 grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="size-4 text-blue-400" />
              Click Activity
            </CardTitle>
          </CardHeader>
          <CardContent>
            {totalUrlsCount === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <BarChart3 className="mb-3 size-10 text-zinc-600" />
                <p className="text-sm text-muted-foreground">No click data yet</p>
                <p className="mt-1 text-xs text-zinc-600">Create a URL and start tracking clicks.</p>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <p className="text-4xl font-bold gradient-text">{totalUrlsCount}</p>
                <p className="mt-1 text-sm text-muted-foreground">URLs created</p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MousePointerClick className="size-4 text-purple-400" />
              Quick Actions
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Link href="/urls/new">
              <Button className="w-full justify-start gap-2 bg-blue-600 text-white hover:bg-blue-700">
                <Plus className="size-4" /> Create New URL
              </Button>
            </Link>
            <Link href="/urls">
              <Button variant="outline" className="w-full justify-start gap-2">
                <Link2 className="size-4" /> View All URLs
              </Button>
            </Link>
            <Link href="/workspaces">
              <Button variant="outline" className="w-full justify-start gap-2">
                <Activity className="size-4" /> Manage Workspaces
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      {error && <p className="mb-4 text-sm text-red-400">{error}</p>}

      {quota && quota.limit > 0 && quota.used / quota.limit > 0.8 && (
        <Card className="mb-6 border-amber-500/30 bg-amber-500/10">
          <CardContent className="flex items-center gap-3 pt-6">
            <AlertTriangle className="size-5 text-amber-400" />
            <div className="flex-1">
              <p className="text-sm font-medium text-amber-300">API rate limit nearly reached</p>
              <p className="text-xs text-amber-200/70">{quota.used} / {quota.limit} requests used</p>
            </div>
            <Link href="/billing"><Button variant="outline" size="sm">Upgrade</Button></Link>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Recent URLs</CardTitle>
          <Link href="/urls"><Button variant="ghost" size="sm">View all</Button></Link>
        </CardHeader>
        <CardContent>
          {urlList.length === 0 ? (
            <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-zinc-700 p-12 text-center">
              <Link2 className="mb-3 size-10 text-zinc-600" />
              <p className="text-muted-foreground">No URLs yet</p>
              <p className="mt-1 text-sm text-zinc-600">Create your first shortened URL to get started.</p>
              <Link href="/urls/new" className="mt-4">
                <Button className="bg-blue-600 text-white hover:bg-blue-700">
                  <Plus className="mr-1 size-4" />Create URL
                </Button>
              </Link>
            </div>
          ) : (
            <div className="space-y-2">
              {urlList.slice(0, 5).map((url) => (
                <div key={url.id} className="flex items-center justify-between rounded-lg border bg-card px-4 py-3 transition-colors hover:bg-muted/50">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <a href={`/${url.short_code}`} target="_blank" className="text-sm font-medium text-blue-400 hover:underline">
                        {url.short_code} <ExternalLink className="inline size-3" />
                      </a>
                      <Badge variant={url.status === "active" ? "success" : "secondary"}>{url.status}</Badge>
                      {url.is_one_time && <Badge variant="warning">One-time</Badge>}
                    </div>
                    <p className="truncate text-xs text-muted-foreground">{url.original_url}</p>
                  </div>
                  <div className="flex items-center gap-1">
                    <Link href={`/urls/${url.id}/analytics`}>
                      <Button variant="ghost" size="xs"><BarChart3 className="size-3.5" /></Button>
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
