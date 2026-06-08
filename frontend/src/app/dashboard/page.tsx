"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { auth, urls, workspaces } from "@/lib/api"
import { useAuthStore } from "@/store/auth"

interface URLItem {
  id: number
  short_code: string
  original_url: string
  created_at: string
}

export default function DashboardPage() {
  const router = useRouter()
  const { user, setUser, isLoading, logout } = useAuthStore()
  const [urlList, setUrlList] = useState<URLItem[]>([])
  const [wsId, setWsId] = useState<number | null>(null)
  const [error, setError] = useState("")

  useEffect(() => {
    auth.me().then(setUser).catch(() => router.push("/login"))
  }, [])

  useEffect(() => {
    if (!user) return
    workspaces.list().then((ws) => {
      if (ws.length > 0) {
        setWsId(ws[0].id)
        urls.list(ws[0].id).then(setUrlList).catch((e) => setError(e.message))
      }
    })
  }, [user])

  if (isLoading) return <div className="flex min-h-screen items-center justify-center">Loading...</div>
  if (!user) return null

  async function handleDelete(id: number) {
    await urls.delete(id)
    if (wsId) urls.list(wsId).then(setUrlList)
  }

  return (
    <div className="min-h-screen bg-zinc-50">
      <header className="flex items-center justify-between border-b bg-white px-6 py-3">
        <h1 className="text-lg font-semibold">LinkForge</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-zinc-500">{user.email}</span>
          <Button variant="outline" size="sm" onClick={() => { logout(); router.push("/login") }}>
            Logout
          </Button>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-4 py-8">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-xl font-semibold">Your URLs</h2>
          <Link href="/urls/new">
            <Button>Create URL</Button>
          </Link>
        </div>

        {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

        {urlList.length === 0 ? (
          <div className="rounded-xl border-2 border-dashed bg-white p-12 text-center">
            <p className="text-zinc-500">No URLs yet. Create your first one!</p>
          </div>
        ) : (
          <div className="space-y-3">
            {urlList.map((url) => (
              <div key={url.id} className="flex items-center justify-between rounded-lg bg-white px-4 py-3 shadow-sm">
                <div className="min-w-0 flex-1">
                  <a
                    href={`http://localhost:8000/${url.short_code}`}
                    target="_blank"
                    className="text-sm font-medium text-blue-600 hover:underline"
                  >
                    {url.short_code}
                  </a>
                  <p className="truncate text-xs text-zinc-400">{url.original_url}</p>
                </div>
                <Button variant="destructive" size="xs" onClick={() => handleDelete(url.id)}>
                  Delete
                </Button>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
