import { useAuth } from '../context/AuthContext'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Button from '../Components/ui/button'
import Input from '../Components/ui/input'
import { Brain } from 'lucide-react'
import client from '../Api/client'

type Step = 'login' | 'otp'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()

  const [step, setStep] = useState<Step>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [otp, setOtp] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [resendLoading, setResendLoading] = useState(false)
  const [resendMsg, setResendMsg] = useState('')

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (password.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }

    setLoading(true)
    try {
      const captchaToken = await (window as any).grecaptcha?.execute(
        import.meta.env.VITE_RECAPTCHA_SITE_KEY,
        { action: 'login' }
      ) ?? ''

      await login(email, password, captchaToken)
      navigate('/chat')
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'Login failed'
   
      if (err.response?.data?.status === 'unverified') {
        setStep('otp')
        return
      }
      setError(detail)
    } finally {
      setLoading(false)
    }
  }

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await client.post('/auth/verify-otp', { email, otp })
      navigate('/chat')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid OTP')
    } finally {
      setLoading(false)
    }
  }

  const handleResendOtp = async () => {
    setResendLoading(true)
    setResendMsg('')
    try {
      await client.post('/auth/resend-otp', { email })
      setResendMsg('OTP resent successfully')
    } catch {
      setResendMsg('Failed to resend OTP')
    } finally {
      setResendLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#111111] flex items-center justify-center">
      <div className="bg-[#1c1c1e] border border-[#2a2a2a] rounded-2xl p-9 w-full max-w-sm">


        <div className="flex items-center gap-3 mb-7">
          <div className="w-11 h-11 bg-[#534AB7] rounded-xl flex items-center justify-center">
            <Brain size={20} color="white" />
          </div>
          <span className="text-lg font-semibold text-white">ResearchMind</span>
        </div>


        {step === 'login' && (
          <>
            <h1 className="text-2xl font-bold text-white mb-1">Welcome back</h1>
            <p className="text-sm text-[#888] mb-7">Sign in to your knowledge base</p>

            <form onSubmit={handleLogin} className="flex flex-col gap-4">
              <Input
                label="Email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
              />
              <Input
                label="Password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
              />

              {error && <p className="text-xs text-red-400">{error}</p>}

              <Button type="submit" disabled={loading} className="w-full">
                {loading ? 'Signing in...' : 'Sign in'}
              </Button>
            </form>

            <div className="flex items-center gap-3 my-5">
              <hr className="flex-1 border-[#2a2a2a]" />
              <span className="text-xs text-[#555]">or</span>
              <hr className="flex-1 border-[#2a2a2a]" />
            </div>

            <Button
              variant="ghost"
              className="w-full"
             onClick={() => window.location.href = `${import.meta.env.VITE_API_URL}/auth/google/login`}
            >
              <img src="https://www.google.com/favicon.ico" width="16" height="16" alt="G" />
              Continue with Google
            </Button>

            <p className="text-xs text-[#555] text-center mt-5">
              Don't have an account?{' '}
              <Link to="/register" className="text-[#7C75D4] hover:underline">Sign up</Link>
            </p>
          </>
        )}

        {/* OTP step */}
        {step === 'otp' && (
          <>
            <h1 className="text-2xl font-bold text-white mb-1">Verify your email</h1>
            <p className="text-sm text-[#888] mb-2">
              We sent a 6-digit code to
            </p>
            <p className="text-sm text-[#7C75D4] mb-7">{email}</p>

            <form onSubmit={handleVerifyOtp} className="flex flex-col gap-4">
              <Input
                label="Verification code"
                placeholder="123456"
                value={otp}
                onChange={e => setOtp(e.target.value)}
                className="text-center text-xl tracking-widest"
              />

              {error && <p className="text-xs text-red-400">{error}</p>}
              {resendMsg && <p className="text-xs text-green-400">{resendMsg}</p>}

              <Button type="submit" disabled={loading || otp.length !== 6} className="w-full">
                {loading ? 'Verifying...' : 'Verify email'}
              </Button>
            </form>

            <div className="flex items-center justify-between mt-4">
              <button
                onClick={() => { setStep('login'); setOtp(''); setError('') }}
                className="text-xs text-[#555] hover:text-white transition-colors"
              >
                ← Back to login
              </button>
              <button
                onClick={handleResendOtp}
                disabled={resendLoading}
                className="text-xs text-[#7C75D4] hover:underline disabled:opacity-40"
              >
                {resendLoading ? 'Sending...' : 'Resend code'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}