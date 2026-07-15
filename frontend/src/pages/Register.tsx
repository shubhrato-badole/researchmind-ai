import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import Input from "../Components/ui/input"
import Button from "../Components/ui/button"
import { useAuth } from "../context/AuthContext"
import client from "../Api/client"
import { Brain } from 'lucide-react'

type Step = 'form' | 'otp'

export default function Register() {
  const { signup } = useAuth()
  const navigate = useNavigate()

  const [step, setStep] = useState<Step>('form')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const [otp, setOtp] = useState('')
  const [otpError, setOtpError] = useState('')
  const [verifying, setVerifying] = useState(false)
  const [resending, setResending] = useState(false)
  const [resendCooldown, setResendCooldown] = useState(0)

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const captchaToken = await (window as any).grecaptcha.execute(
        import.meta.env.VITE_RECAPTCHA_SITE_KEY,
        { action: 'signup' }
      )
      await signup(name, email, password, captchaToken)
      setStep('otp')
      startCooldown()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Signup failed')
    } finally {
      setLoading(false)
    }
  }

  const startCooldown = () => {
    setResendCooldown(30)
    const interval = setInterval(() => {
      setResendCooldown(prev => {
        if (prev <= 1) {
          clearInterval(interval)
          return 0
        }
        return prev - 1
      })
    }, 1000)
  }

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault()
    if (otp.length !== 6) return
    setOtpError('')
    setVerifying(true)
    try {
      await client.post('/auth/verify-otp', { email, otp })
      navigate('/chat')
    } catch (err: any) {
      setOtpError(err.response?.data?.detail || 'Invalid or expired code')
    } finally {
      setVerifying(false)
    }
  }

  const handleResend = async () => {
    if (resendCooldown > 0) return
    setResending(true)
    try {
      await client.post('/auth/resend-otp', { email })
      startCooldown()
    } finally {
      setResending(false)
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

        {step === 'form' ? (
          <>
            <h1 className="text-2xl font-bold mb-1 text-white">Create account</h1>
            <p className="text-sm text-[#888] mb-7">Build your personal AI knowledge base</p>

            <form onSubmit={handleSignup} className="flex flex-col gap-4">
              <Input
                label="Full name"
                type="text"
                placeholder="name"
                value={name}
                onChange={e => setName(e.target.value)}
              />
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
                placeholder="At least 8 characters"
                value={password}
                onChange={e => setPassword(e.target.value)}
              />
              {error && <p className="text-xs text-red-500">{error}</p>}
              <Button type="submit" disabled={loading} className="w-full">
                {loading ? 'Creating account...' : 'Create account'}
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
             onClick={() => window.location.href = '/api/auth/google/login'}
            >
              <img src="https://www.google.com/favicon.ico" width="16" height="16" alt="G" />
              Continue with Google
            </Button>

            <p className="text-xs text-gray-400 text-center mt-4">
              Already have an account?{' '}
              <Link to="/login" className="text-[#534AB7] hover:underline">Sign in</Link>
            </p>
          </>
        ) : (
          <>
            <h1 className="text-2xl font-bold mb-1 text-white">Verify your email</h1>
            <p className="text-sm text-[#888] mb-7">
              We sent a 6-digit code to <span className="text-white">{email}</span>
            </p>

            <form onSubmit={handleVerifyOtp} className="flex flex-col gap-4">
              <input
                value={otp}
                onChange={e => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="000000"
                inputMode="numeric"
                autoFocus
                className="w-full bg-[#2d2d2f] border border-[#3a3a3c] rounded-lg px-4 py-3 text-center text-2xl tracking-[0.5em] text-white outline-none focus:border-[#534AB7] transition-colors"
              />
              {otpError && <p className="text-xs text-red-500">{otpError}</p>}
              <Button type="submit" disabled={otp.length !== 6 || verifying} className="w-full">
                {verifying ? 'Verifying...' : 'Verify and continue'}
              </Button>
            </form>

            <p className="text-xs text-gray-400 text-center mt-4">
              Didn't get the code?{' '}
              <button
                onClick={handleResend}
                disabled={resendCooldown > 0 || resending}
                className="text-[#534AB7] hover:underline disabled:text-[#555] disabled:no-underline"
              >
                {resendCooldown > 0 ? `Resend in ${resendCooldown}s` : resending ? 'Sending...' : 'Resend code'}
              </button>
            </p>

            <button
              onClick={() => setStep('form')}
              className="text-xs text-[#666] hover:text-white transition-colors mt-3 w-full text-center"
            >
              ← Back to signup
            </button>
          </>
        )}
      </div>
    </div>
  )
}