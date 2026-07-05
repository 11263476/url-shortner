import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen } from "@testing-library/react"
import DashboardPage from "@/app/(authenticated)/dashboard/page"

vi.mock("@/hooks/useDashboard", () => ({
  useDashboard: () => ({
    urlList: [],
    totalUrlsCount: 0,
    workspaces: [],
    wsId: null,
    error: null,
    quota: null,
    canEdit: true,
    activeUrls: [],
    isLoading: false,
    setWsId: vi.fn(),
  }),
}))

vi.mock("@/queries", () => ({
  useMe: () => ({ data: { id: 1, email: "test@test.com" } }),
  useWorkspaces: () => ({ data: [] }),
  useWorkspaceMembers: () => ({ data: [] }),
  useUrls: () => ({ data: { items: [], total: 0 }, error: null }),
  useFolders: () => ({ data: [] }),
  useTags: () => ({ data: [] }),
  useFavorites: () => ({ data: [] }),
  useDeleteUrlMutation: () => ({ mutate: vi.fn(), mutateAsync: vi.fn() }),
  useAddFavoriteMutation: () => ({ mutate: vi.fn() }),
  useRemoveFavoriteMutation: () => ({ mutate: vi.fn() }),
  useApiKeys: () => ({ data: [], isLoading: false }),
  useApiKeyQuota: () => ({ data: null }),
}))

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}))

describe("DashboardPage", () => {
  beforeEach(() => {
    document.title = ""
  })

  it("renders dashboard title", () => {
    render(<DashboardPage />)
    expect(screen.getByText("Dashboard")).toBeDefined()
  })

  it("renders stats cards", () => {
    render(<DashboardPage />)
    expect(screen.getByText("Total URLs")).toBeDefined()
    expect(screen.getByText("Active")).toBeDefined()
  })

  it("shows view all link", () => {
    render(<DashboardPage />)
    expect(screen.getByText("View all")).toBeDefined()
  })

  it("shows no URLs message when empty", () => {
    render(<DashboardPage />)
    expect(screen.getByText(/No URLs yet/i)).toBeDefined()
  })

  it("sets document title", () => {
    render(<DashboardPage />)
    expect(document.title).toBe("Dashboard - LinkForge")
  })
})
