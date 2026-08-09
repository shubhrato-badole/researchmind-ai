import { useNavigate } from 'react-router-dom'
import { X, Check, Brain, ShieldCheck } from 'lucide-react'
import Layout from '../Components/Layout'
import UpgradeButton from '../Components/UpgradeButton'
import { useAuth } from '../context/AuthContext'

const FREE_FEATURES = [
  '10 doc searches / day',
  '10 web searches / day',
  '1 roadmap (30-day cooldown)',
  '2 quizzes / day',
  '5 document uploads'
]

const PRO_FEATURES = [
  'Unlimited doc + web search',
  'Unlimited roadmaps',
  'Unlimited quizzes',
  'Unlimited uploads',
  'Voice search + priority speed'
]

export default function Pricing() {
  const navigate = useNavigate()
  const { user } = useAuth()

  return (
    <Layout>
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="px-5 py-3 border-b border-[#3a3a3c] bg-[#2d2d2f] flex items-center justify-between flex-shrink-0">
          <h1 className="text-sm font-semibold text-white">Plans</h1>
          <button onClick={() => navigate(-1)} className="text-[#888] hover:text-white transition-colors">
            <X size={18} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 bg-[#2d2d2f]">
          <div className="text-center mb-6">
            <div className="w-12 h-12 bg-[#534AB7] rounded-xl flex items-center justify-center mx-auto mb-3">
              <Brain size={24} color="white" />
            </div>
            <h2 className="text-lg font-semibold text-white mb-1">Choose your plan</h2>
            <p className="text-xs text-[#888]">Start free, upgrade when you need more room to research</p>
          </div>

          <div className="max-w-xl mx-auto grid grid-cols-2 gap-4">

            <div className="bg-[#1c1c1e] border border-[#2a2a2a] rounded-2xl p-6">
              <p className="text-white font-medium mb-1">Free</p>
              <p className="text-2xl font-semibold text-white mb-0.5">₹0</p>
              <p className="text-[11px] text-[#666] mb-4">Forever</p>
              <div className="flex flex-col gap-2.5">
                {FREE_FEATURES.map(f => (
                  <span key={f} className="text-xs text-[#ccc] flex items-center gap-1.5">
                    <Check size={14} className="text-[#5DCAA5] flex-shrink-0" /> {f}
                  </span>
                ))}
              </div>
            </div>

            <div className="bg-[#1c1c1e] border-2 border-[#7F77DD] rounded-2xl p-6 relative">
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-[#7F77DD] text-[#26215C] text-[11px] px-3 py-0.5 rounded-full">
                Most popular
              </span>
              <p className="text-white font-medium mb-1">Pro</p>
              <p className="text-2xl font-semibold text-white mb-0.5">
                ₹249<span className="text-xs text-[#888]">/mo</span>
              </p>
              <p className="text-[11px] text-[#7F77DD] mb-4">Cancel anytime</p>
              <div className="flex flex-col gap-2.5 mb-5">
                {PRO_FEATURES.map(f => (
                  <span key={f} className="text-xs text-[#ccc] flex items-center gap-1.5">
                    <Check size={14} className="text-[#AFA9EC] flex-shrink-0" /> {f}
                  </span>
                ))}
              </div>
              {user?.plan === 'pro' ? (
                <p className="text-xs text-[#5DCAA5] text-center">You're on Pro</p>
              ) : (
                <UpgradeButton />
              )}
            </div>

          </div>

          <div className="max-w-xl mx-auto flex items-center justify-center gap-2 text-[#666] text-xs mt-6">
            <ShieldCheck size={15} />
            Secured by Razorpay · Cancel anytime from your profile
          </div>
        </div>
      </div>
    </Layout>
  )
}