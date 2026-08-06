import { createContext, useContext, useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '../Api/client'

interface User {
  id: number
  name: string
  email: string
  plan: 'free' | 'pro'
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string, captchaToken: string) => Promise<User>
  signup: (name: string, email: string, password: string, captchaToken: string) => Promise<User>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    const getUser = async () => {
      try {
        const res = await client.get('/auth/me')
        setUser(res.data.user)
      } catch {
        setUser(null)
      } finally {
        setLoading(false)
      }
    }
    getUser()
  }, [])

  const login = async (email: string, password: string, captchaToken: string) => {
    const res = await client.post("auth/login",{ email, password, captcha_token: captchaToken })
    setUser(res.data.user)
    return res.data.user
  }

  const signup = async (name: string, email: string, password: string, captchaToken: string) => {
    const res = await client.post("auth/signup",{ name, email, password, captcha_token: captchaToken })
    setUser(res.data.user)
    return res.data.user
  }

  const logout = async () => {
    await client.post("auth/logout")
    setUser(null)
    navigate("/login")
  }

  return (
    <AuthContext.Provider value={{ user, login, signup, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside AuthProvider')
  return context
}