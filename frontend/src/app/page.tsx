import Link from "next/link"

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-zinc-50 px-4">
      <div className="max-w-lg text-center">
        <h1 className="mb-4 text-4xl font-bold tracking-tight">LinkForge</h1>
        <p className="mb-8 text-lg text-zinc-500">
          Enterprise-grade URL shortener with analytics, team collaboration, and observability.
        </p>
        <div className="flex justify-center gap-4">
          <Link
            href="/login"
            className="inline-flex h-10 items-center rounded-lg bg-zinc-900 px-6 text-sm font-medium text-white hover:bg-zinc-800"
          >
            Get Started
          </Link>
          <Link
            href="/login"
            className="inline-flex h-10 items-center rounded-lg border bg-white px-6 text-sm font-medium hover:bg-zinc-50"
          >
            Sign In
          </Link>
        </div>
      </div>
    </div>
  )
}
