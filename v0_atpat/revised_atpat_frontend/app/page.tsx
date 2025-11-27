"use client"

import { useAuth } from "@/lib/auth-context"
import { usePathname, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { useEffect } from "react"

export default function Home() {
  const { user, loading } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    if (!loading) {
      router.replace(pathname)
    }
  }, [user, loading, router])


  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>
  }

  const handleCreateTest = () => {
    if (user?.role === "admin") {
      router.push("/tests/new")
    } else {
      router.push("/login")
    }
  }

  const handleOpenDashboard = () => {
    if (!user) {
      router.push("/login")
    } else if (user.role === "student") {
      router.push("/tests") // route for student view
    } else if (user.role === "admin") {
      router.push("/tests") // route for admin view
    }
  }

  console.log("Logged in user role:", user?.role)

  return (
    <main className="max-w-7xl mx-auto px-4 py-12">
      <div className="mb-12">
        <h1 className="text-4xl font-bold mb-2">ATPAT Proctoring Portal</h1>
        <p className="text-gray-600">
          Admins can create tests and view reports. Students can review proctoring flags and submit reconsiderations.
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <Card className="p-6">
          <h2 className="text-xl font-bold mb-2">Create a Test</h2>
          <p className="text-gray-600 mb-4">
            Set parent test URL, duration, login window, and upload students CSV.
          </p>
          <Button onClick={handleCreateTest}>Create Test</Button>
        </Card>

        <Card className="p-6">
          <h2 className="text-xl font-bold mb-2">Open Dashboard</h2>
          <p className="text-gray-600 mb-4">
            Browse existing tests and check their status. Review flags if applicable.
          </p>
          <Button variant="outline" onClick={handleOpenDashboard}>
            Open Dashboard
          </Button>
        </Card>
      </div>
    </main>
  )
}
