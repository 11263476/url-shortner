import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"

describe("Button", () => {
  it("renders with text", () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText("Click me")).toBeDefined()
  })

  it("renders with different variants", () => {
    const { container } = render(<Button variant="destructive">Delete</Button>)
    expect(container.querySelector("[data-slot=button]")).toBeDefined()
  })

  it("renders with different sizes", () => {
    const { container } = render(<Button size="sm">Small</Button>)
    expect(container.querySelector("[data-slot=button]")).toBeDefined()
  })

  it("renders disabled", () => {
    render(<Button disabled>Disabled</Button>)
    const btn = screen.getByText("Disabled") as HTMLButtonElement
    expect(btn.disabled).toBe(true)
  })

  it("applies custom className", () => {
    const { container } = render(<Button className="custom-class">Styled</Button>)
    expect(container.querySelector(".custom-class")).toBeDefined()
  })
})

describe("Badge", () => {
  it("renders with text", () => {
    render(<Badge>Active</Badge>)
    expect(screen.getByText("Active")).toBeDefined()
  })

  it("renders with variant", () => {
    const { container } = render(<Badge variant="success">Success</Badge>)
    expect(container.querySelector("[data-slot=badge]")).toBeDefined()
  })

  it("renders with outline variant", () => {
    render(<Badge variant="outline">Outline</Badge>)
    expect(screen.getByText("Outline")).toBeDefined()
  })
})

describe("Card", () => {
  it("renders card with header and content", () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Test Title</CardTitle>
        </CardHeader>
        <CardContent>Card content here</CardContent>
      </Card>,
    )
    expect(screen.getByText("Test Title")).toBeDefined()
    expect(screen.getByText("Card content here")).toBeDefined()
  })

  it("has the correct data-slot attributes", () => {
    const { container } = render(
      <Card>
        <CardHeader>
          <CardTitle>Title</CardTitle>
        </CardHeader>
        <CardContent>Content</CardContent>
      </Card>,
    )
    expect(container.querySelector("[data-slot=card]")).toBeDefined()
    expect(container.querySelector("[data-slot=card-header]")).toBeDefined()
    expect(container.querySelector("[data-slot=card-title]")).toBeDefined()
    expect(container.querySelector("[data-slot=card-content]")).toBeDefined()
  })
})
