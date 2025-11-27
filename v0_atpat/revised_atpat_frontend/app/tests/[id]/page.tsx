"use client"

import { useEffect, useState } from "react"
import { useAuth } from "@/lib/auth-context"
import { useRouter, useParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { api } from "@/lib/api"

interface StudentFlagSummary {
  mis_id: string
  student_name?: string
  student_email?: string
  to_review: boolean
}

export default function TestDetailPage() {
  const { user, loading } = useAuth()
  const router = useRouter()
  const params = useParams()
  const testId = params.id as string

  const [students, setStudents] = useState<StudentFlagSummary[]>([])
  const [pageLoading, setPageLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    if (!loading && !user) router.push("/login")
  }, [user, loading, router])

  useEffect(() => {
    if (user && testId) fetchStudentList()
  }, [user, testId])

  const fetchStudentList = async () => {
    try {
      const data = await api.flags.getFlags(testId)
      if (data.status === "success") {
        const sorted = data.flags.sort((a: any, b: any) =>
          b.to_review === a.to_review ? 0 : b.to_review ? 1 : -1
        )
        setStudents(sorted)
      } else {
        setError("Failed to load student list")
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load student list")
    } finally {
      setPageLoading(false)
    }
  }

  const toggleReview = async (student: StudentFlagSummary) => {
    try {
      const response = await api.flags.updateReview(testId, student.mis_id, !student.to_review)
      if (response.status === "success") {
        setStudents((prev) =>
          prev
            .map((s) =>
              s.mis_id === student.mis_id ? { ...s, to_review: !s.to_review } : s
            )
            .sort((a, b) => (b.to_review === a.to_review ? 0 : b.to_review ? 1 : -1))
        )
      } else setError("Failed to update review status")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update review status")
    }
  }

  const deleteFlag = async (student: StudentFlagSummary) => {
    if (!confirm(`Are you sure you want to delete ${student.student_name || student.mis_id}'s flag?`)) return
    try {
      const response = await api.flags.deleteFlag(testId, student.mis_id)
      if (response.status === "success") {
        setStudents((prev) => prev.filter((s) => s.mis_id !== student.mis_id))
      } else {
        setError("Failed to delete flag")
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete flag")
    }
  }

  if (loading || pageLoading)
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>

  if (!user) return null

  return (
    <main className="max-w-6xl mx-auto px-4 py-12">
      <div className="mb-8">
        <Button variant="outline" onClick={() => router.back()}>
          ← Back
        </Button>
      </div>

      <Card className="p-6 mb-6">
        <h1 className="text-3xl font-bold mb-2">Test Overview</h1>
        <p className="text-gray-600">
          {user.role === "admin"
            ? "Select a student to view their flag summary."
            : "Your test activity summary."}
        </p>
      </Card>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded text-red-700">{error}</div>
      )}

      <Card className="p-6">
        <h2 className="text-2xl font-bold mb-4">Students</h2>

        {students.length > 0 ? (
          <div className="space-y-3">
            {students.map((s) => (
              <div
                key={s.mis_id} // ✅ FIXED: stable key instead of index
                className={`p-4 border rounded-lg cursor-pointer transition ${
                  s.to_review
                    ? "border-green-500 bg-green-50 hover:bg-green-100"
                    : "border-gray-300 bg-gray-50 hover:bg-gray-100"
                }`}
                onClick={() => router.push(`/tests/${testId}/${s.mis_id}`)}
              >
                <div className="flex justify-between items-center">
                  <div>
                    <p className="font-semibold">{s.student_name || "Unknown Student"}</p>
                    <p className="text-sm text-gray-600">{s.student_email || "No email"}</p>
                  </div>

                  <div className="flex items-center gap-3">
                    <Button
                      variant={s.to_review ? "default" : "outline"}
                      onClick={(e) => {
                        e.stopPropagation()
                        toggleReview(s)
                      }}
                    >
                      {s.to_review ? "Marked for Review" : "Not Marked"}
                    </Button>

                    {user.role === "admin" && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="bg-black text-white hover:bg-gray-800"
                        onClick={(e) => {
                          e.stopPropagation()
                          deleteFlag(s)
                        }}
                      >
                        Delete
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-600">No student data available for this test.</p>
        )}
      </Card>
    </main>
  )
}
