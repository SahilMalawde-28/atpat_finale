//const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000/api"

const API_BASE = "/api";

export const api = {

  async request(endpoint: string, options: RequestInit = {}) {
    // 🧩 Skip setting Content-Type if body is FormData
    const isFormData = options.body instanceof FormData
  
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: isFormData
        ? options.headers // let browser handle multipart boundary
        : {
            "Content-Type": "application/json",
            ...options.headers,
          },
      credentials: "include",
    })
  
    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.message || `API error: ${response.status}`)
    }
  
    return response.json()
  },
  

  auth: {
    login: (email: string, password: string, role: string) =>
      api.request("/auth_routes/login", {
        method: "POST",
        body: JSON.stringify({ email, password, role }),
      }),

    signup: (name: string, email: string, mis_id: string, password: string, role: string) =>
      api.request("/auth_routes/signup", {
        method: "POST",
        body: JSON.stringify({ name, email, mis_id, password, role }),
      }),

    logout: () => api.request("/auth_routes/logout", { method: "POST" }),

    me: () => api.request("/auth_routes/me"),
  },

  tests: {
    create: (data: any) =>
      api.request("/tests", {
        method: "POST",
        body: data instanceof FormData ? data : JSON.stringify(data),
        headers: data instanceof FormData ? {} : { "Content-Type": "application/json" },
      }),

    list: () => api.request("/tests"),

    adminList: () => api.request("/test_routes/showtestsadmin"),

    get: (id: string) => api.request(`/test_routes/${id}`),

    studentList: () => api.request("/test_routes/showtestsstudents")

  },

  flags: {
    getFlags: (test_id: string) =>
      api.request("/flag_routes/getflag", {
        method: "POST",
        body: JSON.stringify({ test_id }),
      }),
  
    updateReview: (test_id: string, mis_id: string, to_review: boolean) =>
      api.request("/flag_routes/updateReview", {
        method: "POST",
        body: JSON.stringify({ test_id, mis_id, to_review }),
      }),

    deleteFlag: (test_id: string, mis_id: string) =>
      api.request("/flag_routes/deleteFlag", {
        method: "DELETE",
        body: JSON.stringify({ test_id, mis_id }),
      }),

  },
  
}