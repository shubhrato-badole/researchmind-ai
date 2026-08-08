import { useNavigate } from 'react-router-dom'
import { X } from 'lucide-react'
import Layout from '../Components/Layout'
import UpgradeButton from '../Components/UpgradeButton'
import { useAuth } from '../context/AuthContext'

export default function Pricing() {
  const navigate = useNavigate()
  const { user } = useAuth()

  return (
    <Layout>
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="px-5 py-3 border-b border-[#3a3a3c] bg-[#2d2d2f] flex items-center justify-between">
          <h1 className="text-sm font-semibold text-white">Plans</h1>
          <button onClick={() => navigate(-1)} className="text-[#888] hover:text-white">
            <X size={18} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 bg-[#2d2d2f]">
          <div className="max-w-2xl mx-auto grid grid-cols-2 gap-4">

            <div className="bg-[#1c1c1e] border border-[#2a2a2a] rounded-2xl p-6">
              <p className="text-white font-medium mb-1">Free</p>
              <p className="text-2xl font-semibold text-white mb-4">₹0</p>
              <ul className="text-xs text-[#ccc] flex flex-col gap-2">
                <li>10 doc searches / day</li>
                <li>10 web searches / day</li>
                <li>1 roadmap (30-day cooldown)</li>
                <li>2 quizzes / day</li>
                <li>5 document uploads</li>
              </ul>
            </div>

            <div className="bg-[#1c1c1e] border-2 border-[#7F77DD] rounded-2xl p-6 relative">
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-[#7F77DD] text-[#26215C] text-[11px] px-3 py-0.5 rounded-full">Most popular</span>
              <p className="text-white font-medium mb-1">Pro</p>
              <p className="text-2xl font-semibold text-white mb-4">₹249<span className="text-xs text-[#888]">/mo</span></p>
              <ul className="text-xs text-[#ccc] flex flex-col gap-2 mb-5">
                <li>Unlimited doc + web search</li>
                <li>Unlimited roadmaps</li>
                <li>Unlimited quizzes</li>
                <li>Unlimited uploads</li>
                <li>Voice search + priority speed</li>
              </ul>
              {user?.plan === 'pro' ? (
                <p className="text-xs text-[#5DCAA5]">You're on Pro</p>
              ) : (
                <UpgradeButton />
              )}
            </div>

          </div>
        </div>
      </div>
    </Layout>
  )
}