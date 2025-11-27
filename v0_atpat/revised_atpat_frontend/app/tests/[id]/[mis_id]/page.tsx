"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { api } from "@/lib/api"

interface Proof {
  path: string
  ts: number
  type: string
}

interface StudentFlag {
  mis_id: string
  student_name: string
  student_email: string
  start_time: string
  end_time: string
  alt_tab: number
  audio_events: number
  avg_wpm: number
  backspace_ratio: number
  multi_face: number
  no_face: number
  off_gaze: number
  parenturl: string
  typing_events: number
  typing_flags: number
  to_review: boolean
  proofs: Proof[]
}

export default function StudentFlagDetailPage() {
  const params = useParams()
  const router = useRouter()
  const testId = params.id as string
  const misId = params.mis_id as string

  const [studentData, setStudentData] = useState<StudentFlag | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    fetchStudentData()
  }, [testId, misId])

  const fetchStudentData = async () => {
    try {
      const data = await api.flags.getFlags(testId)
      if (data.status === "success") {
        const student = data.flags.find((f: any) => f.mis_id === misId)
        if (student) setStudentData(student)
        else setError("Student data not found for this test.")
      } else {
        setError("Failed to fetch flag data.")
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch data.")
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="flex justify-center items-center min-h-screen">Loading...</div>
  if (error)
    return (
      <div className="flex flex-col items-center justify-center min-h-screen text-red-600">
        <p>{error}</p>
        <Button variant="outline" onClick={() => router.back()} className="mt-4">
          ← Back
        </Button>
      </div>
    )

  if (!studentData) return null

  const {
    student_name,
    student_email,
    start_time,
    end_time,
    avg_wpm,
    backspace_ratio,
    alt_tab,
    audio_events,
    typing_events,
    typing_flags,
    multi_face,
    no_face,
    off_gaze,
    parenturl,
    proofs,
    to_review,
  } = studentData

  return (
    <main className="max-w-5xl mx-auto px-4 py-10">
      <Button variant="outline" onClick={() => router.back()} className="mb-6">
        ← Back
      </Button>

      <Card className="p-6 space-y-4">
        <h1 className="text-3xl font-bold mb-4">Student Report</h1>

        <div>
          <p className="font-semibold text-lg">{student_name}</p>
          <p className="text-gray-600">{student_email}</p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mt-4">
          <div>🕒 <strong>Start:</strong> {start_time}</div>
          <div>🕒 <strong>End:</strong> {end_time}</div>
          <div>🌐 <strong>Parent URL:</strong> {parenturl}</div>
          <div>⌨️ <strong>Avg WPM:</strong> {avg_wpm}</div>
          <div>⌫ <strong>Backspace Ratio:</strong> {backspace_ratio}</div>
          <div>🪟 <strong>Alt+Tab:</strong> {alt_tab}</div>
          <div>🔊 <strong>Audio Events:</strong> {audio_events}</div>
          <div>👀 <strong>No Face:</strong> {no_face}</div>
          <div>👥 <strong>Multiple Faces:</strong> {multi_face}</div>
          <div>↘️ <strong>Off Gaze:</strong> {off_gaze}</div>
          <div>⌨️ <strong>Typing Events:</strong> {typing_events}</div>
          <div>⚠️ <strong>Typing Flags:</strong> {typing_flags}</div>
          <div>
            🟩 <strong>Review Status:</strong>{" "}
            {to_review ? "Marked for Review" : "Not Marked"}
          </div>
        </div>

        <div className="mt-6">
          <h2 className="text-xl font-semibold mb-2">Proofs</h2>
          {proofs && proofs.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {proofs.map((p, i) => (
                <Card key={i} className="p-3 border rounded-lg">
                  <p className="text-sm text-gray-600">
                    <strong>Type:</strong> {p.type}
                  </p>
                  <p className="text-sm text-gray-600">
                    <strong>Timestamp:</strong> {new Date(p.ts).toLocaleString()}
                  </p>
                  <p className="text-sm text-gray-600 break-all">
                    <strong>Path:</strong> {p.path}
                  </p>
                </Card>
              ))}
            </div>
          ) : (
            <p className="text-gray-600">No proofs available.</p>
          )}
        </div>
      </Card>
    </main>
  )
}
