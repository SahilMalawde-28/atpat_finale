"use client"

import { useEffect, useState } from "react"
import { useAuth } from "@/lib/auth-context"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { api } from "@/lib/api"

/*interface Test {
  id: string
  name: string
  parent_test_url: string
  login_window_start: string
  login_window_end: string
  status?: string
}*/

type Test = {
  id: string
  name: string
  parenturl: string
  login_window_start: string
  login_window_end: string
}

export default function TestsPage() {
  const { user, loading } = useAuth()
  const router = useRouter()
  const [tests, setTests] = useState<Test[]>([])
  const [testLoading, setTestLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login")
    }
  }, [user, loading, router])

  useEffect(() => {
    if (user) {
      fetchTests()
    }
  }, [user])

  /*const fetchTests = async () => {
    try {
      const data = await api.tests.list()
      setTests(data.tests || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load tests")
    } finally {
      setTestLoading(false)
    }
  }*/


  const fetchTests = async () => {
  try {
    let data;

    if (user?.role === "admin") {
      data = await api.tests.adminList();
    } else if (user?.role === "student") {
      data = await api.tests.studentList();
    } else {
      throw new Error("Unknown user role");
    }
    

    setTests(data.tests || []);
  } catch (err) {
    console.error("Error fetching tests:", err);
    setError(err instanceof Error ? err.message : "Failed to load tests");
  } finally {
    setTestLoading(false);
  }
};

  if (loading || testLoading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>
  }

  if (!user) {
    return null
  }

  return (
    <main className="max-w-7xl mx-auto px-4 py-12">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold">All Tests</h1>
        {user.role === "admin" && <Button onClick={() => router.push("/tests/new")}>Create Test</Button>}
      </div>

      {error && <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded text-red-700">{error}</div>}

      <Card className="p-6">
        <h2 className="text-xl font-bold mb-4">
          {user.role === "admin" ? "Your Created Tests" : "Your Registered Tests"}
        </h2>

        {tests.length === 0 ? (
          <p className="text-gray-600">
            {user.role === "admin"
              ? "No tests created yet. Create one to get started."
              : "Not registered in any tests yet."}
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 font-semibold">Test Name</th>
                  <th className="text-left py-3 px-4 font-semibold">Test URL</th>
                  <th className="text-left py-3 px-4 font-semibold">Login Start</th>
                  <th className="text-left py-3 px-4 font-semibold">Login End</th>
                  <th className="text-left py-3 px-4 font-semibold">Action</th>
                </tr>
              </thead>
              <tbody>
                {tests.map((test) => (
                  <tr key={test.id} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4">{test.name || "Unnamed Test"}</td>
                    <td className="py-3 px-4">
                      <a
                        href={test.parenturl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline truncate block max-w-xs"
                      >
                        {test.parenturl}
                      </a>
                    </td>
                    <td className="py-3 px-4 text-sm">{new Date(test.login_window_start).toLocaleString()}</td>
                    <td className="py-3 px-4 text-sm">{new Date(test.login_window_end).toLocaleString()}</td>
                    <td className="py-3 px-4">
                      <Button variant="outline" size="sm" onClick={() => router.push(`/tests/${test.id}`)}>
                        {user.role === "admin" ? "View Flags" : "Review Flags"}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </main>
  )
}
