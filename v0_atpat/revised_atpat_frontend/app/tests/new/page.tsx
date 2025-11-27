"use client"

import type React from "react"
import { useState } from "react"
import { useAuth } from "@/lib/auth-context"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { api } from "@/lib/api"

export default function CreateTestPage() {
  const { user, loading } = useAuth()
  const router = useRouter()
  const [error, setError] = useState("")
  const [submitting, setSubmitting] = useState(false)

  const [formData, setFormData] = useState({
    name: "",
    parent_test_url: "",
    duration: "90",
    login_window_start: "",
    login_window_end: "",
    notes: "",
    send_invites: false,
  })

  const [csvFile, setCsvFile] = useState<File | null>(null)

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>
  }

  if (!user) {
    router.push("/login")
    return null
  }

  if (user.role !== "admin") {
    return (
      <main className="flex items-center justify-center min-h-screen">
        <p className="text-red-600">Only admins can create tests.</p>
      </main>
    )
  }

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target as any
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? (e.target as HTMLInputElement).checked : value,
    }))
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCsvFile(e.target.files?.[0] || null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setSubmitting(true)

    try {
      const data = new FormData()

      // 🧩 Match backend field names
      data.append("testname", formData.name)
      data.append("parenturl", formData.parent_test_url)
      data.append("duration", formData.duration)
      data.append("loginwindowstart", formData.login_window_start)
      data.append("loginwindowend", formData.login_window_end)
      data.append("description", formData.notes)
      data.append("send_invites", formData.send_invites ? "1" : "0")

      if (csvFile) {
        data.append("file", csvFile) // ✅ backend expects "file"
      }

      // ✅ POST to correct endpoint
      await api.request("/test_routes/createtest", {
        method: "POST",
        body: data,
        credentials: "include",
      })

      alert("Test created successfully!")
      router.push("/tests")
    } catch (err) {
      console.error("Error creating test:", err)
      setError(err instanceof Error ? err.message : "Failed to create test")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="max-w-2xl mx-auto px-4 py-12">
      <Card className="p-8">
        <h1 className="text-2xl font-bold mb-2">Create Test</h1>
        <p className="text-gray-600 mb-6">
          Define the test parameters and upload the students CSV (name, email, id).
        </p>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium mb-1">Test name (optional)</label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              placeholder="Midterm - CS101"
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-black"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Parent test URL</label>
            <input
              type="url"
              name="parent_test_url"
              value={formData.parent_test_url}
              onChange={handleInputChange}
              placeholder="https://www.hackerrank.com/..."
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-black"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Duration (minutes)</label>
            <input
              type="number"
              name="duration"
              value={formData.duration}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-black"
              required
            />
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Login window start</label>
              <input
                type="datetime-local"
                name="login_window_start"
                value={formData.login_window_start}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-black"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Login window end</label>
              <input
                type="datetime-local"
                name="login_window_end"
                value={formData.login_window_end}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-black"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Students CSV</label>
            <input
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-black"
              required
            />
            <p className="text-xs text-gray-600 mt-1">
              CSV columns: name, email, mis_id (header row recommended)
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Notes (optional)</label>
            <textarea
              name="notes"
              value={formData.notes}
              onChange={handleInputChange}
              placeholder="Any specific rules or instructions for proctoring..."
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-black"
              rows={4}
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              name="send_invites"
              checked={formData.send_invites}
              onChange={handleInputChange}
              className="w-4 h-4"
            />
            <label className="text-sm">Send invites to students</label>
          </div>

          <div className="flex gap-3">
            <Button type="button" variant="outline" onClick={() => router.back()} disabled={submitting}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Creating..." : "Confirm & Create Test"}
            </Button>
          </div>
        </form>
      </Card>
    </main>
  )
}
