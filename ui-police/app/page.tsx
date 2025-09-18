"use client"

import { useState } from "react"
import { Dashboard } from "@/components/dashboard"
import { LoginPage } from "@/components/login-page"

export default function Home() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  if (!isAuthenticated) {
    return <LoginPage onLogin={() => setIsAuthenticated(true)} />
  }

  return <Dashboard />
}
