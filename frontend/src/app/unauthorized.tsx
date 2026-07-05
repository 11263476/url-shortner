import Link from "next/link"

export default function Unauthorized() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-zinc-950 px-4">
      <h1 className="text-6xl font-bold text-zinc-700">401</h1>
      <p className="mt-3 text-lg text-zinc-400">You need to sign in to access this page.</p>
      <Link
        href="/login"
        className="mt-6 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
      >
        Sign In
      </Link>
    </div>
  )
}
