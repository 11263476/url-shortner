import Link from "next/link"

export default function Forbidden() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-zinc-950 px-4">
      <h1 className="text-6xl font-bold text-zinc-700">403</h1>
      <p className="mt-3 text-lg text-zinc-400">You do not have access to this page.</p>
      <Link
        href="/dashboard"
        className="mt-6 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
      >
        Go to Dashboard
      </Link>
    </div>
  )
}
