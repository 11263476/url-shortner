"use client"

import { useState } from "react"
import { useMe, useWorkspaces, useUrls, useWorkspaceMembers, useApiKeys, useApiKeyQuota, useDeleteUrlMutation } from "@/queries"

export function useDashboard() {
  const { data: user, isLoading: userLoading } = useMe()
  const { data: workspaces = [], isLoading: workspacesLoading } = useWorkspaces()
  const [wsId, setWsId] = useState<number | null>(null)
  const { data: members = [], isLoading: membersLoading } = useWorkspaceMembers(wsId)
  const { data: urlsData, error: urlsError, isLoading: urlsLoading } = useUrls(wsId, { limit: 50 })
  const urlList = urlsData?.items || []
  const totalUrlsCount = urlsData?.total || 0

  const { data: keys = [], isLoading: keysLoading } = useApiKeys()
  const { data: quota } = useApiKeyQuota(keys[0]?.id ?? null)

  const deleteUrl = useDeleteUrlMutation()

  const myRole = members.find(m => m.user_id === user?.id)?.role
  const canEdit = myRole === "admin" || myRole === "editor"
  const isLoading = userLoading || workspacesLoading

  async function handleDelete(id: number) {
    await deleteUrl.mutateAsync(id)
  }

  const activeUrls = urlList.filter((u) => u.status === "active")
  const error = urlsError instanceof Error ? urlsError.message : ""

  return {
    urlList, totalUrlsCount, workspaces, wsId, members, error, quota,
    myRole, canEdit, activeUrls, isLoading,
    setWsId, handleDelete,
  }
}
