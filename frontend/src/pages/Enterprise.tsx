// src/pages/Enterprise.tsx
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Brain, Lock, Building, Users, Cpu, Shield, Clock, BookOpen, DollarSign } from 'lucide-react'
import Button from '../Components/ui/button'
import Input from '../Components/ui/input'

export default function Enterprise() {
  const [form, setForm] = useState({
    name: '', company: '', email: '', teamSize: '', message: ''
  })
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitted(true)
  }

  return (
    <div className="min-h-screen bg-[#2d2d2f] flex flex-col w-full">

   
      <nav className="flex items-center justify-between sticky px-8 py-4 top-0 z-10 bg-[#2d2d2f] border-b border-[#3a3a3c]">
        <div className="flex items-center gap-2">
          <div className="w-9 h-9 bg-[#534AB7] rounded-xl flex items-center justify-center">
            <Brain size={18} color="white" fill="white" />
          </div>
          <span className="font-semibold text-white text-lg">ResearchMind</span>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/" className="text-sm text-[#999] border border-[#555] px-4 py-2 rounded-lg hover:text-white hover:border-[#888] transition-colors">
            ← Back
          </Link>
          <Link to="/register" className="text-sm bg-[#534AB7] text-white px-4 py-2 rounded-lg hover:bg-[#3C3489] transition-colors">
            Get started free
          </Link>
        </div>
      </nav>

      
       <div className="max-w-6xl mx-auto w-full px-8">
      <section className="py-16 border-b border-[#3a3a3c]">
        <div className="max-w-4xl">
          <div className="inline-block text-xs font-medium px-3 py-1 rounded-full bg-[#1e1b4b] text-[#7C75D4] border border-[#534AB7] mb-4">
            Enterprise
          </div>
          <h1 className="text-4xl font-semibold text-white leading-tight max-w-2xl mb-4">
            ResearchMind on your own server.<br />Your data never leaves.
          </h1>
          <p className="text-base text-[#999] max-w-xl leading-relaxed">
            We give you the complete system. You install it inside your company. Your employees use it. Your documents stay private — forever.
          </p>
        </div>
      </section>

      
      <section className="py-14 border-b border-[#3a3a3c]">
        <p className="text-xs font-medium text-[#666] uppercase tracking-widest mb-2">Why ResearchMind Enterprise</p>
        <h2 className="text-2xl font-semibold text-white mb-2">Your employees waste hours searching.<br />Your data cannot leave the building.</h2>
        <p className="text-sm text-[#999] max-w-2xl mb-8">Every company has thousands of documents — policies, case files, reports — that nobody can search properly. The answers exist. They just can't find them. And you can't send that data to ChatGPT.</p>

        <div className="grid grid-cols-2 gap-4 w-full mb-6">
          {[
            {
              icon: Shield,
              title: 'Confidential data risk',
              before: 'Employees upload patient records to ChatGPT — your data goes to OpenAI\'s servers',
              after: 'ResearchMind runs on your server — data never leaves your building. Ever.'
            },
            {
              icon: Clock,
              title: 'Hours lost searching',
              before: 'A new doctor reads through 50 pages of patient history before every appointment',
              after: 'Ask one question, get the full context in 5 seconds with sources cited'
            },
            {
              icon: Users,
              title: 'Knowledge silos',
              before: 'When a senior employee leaves, all their knowledge walks out with them',
              after: 'Everything they documented stays searchable forever in your knowledge base'
            },
            {
              icon: DollarSign,
              title: 'Expensive SaaS tools',
              before: 'Paying per seat per month for tools that still send your data to their cloud',
              after: 'One-time setup on your infrastructure — no recurring per-seat fees'
            },
            {
              icon: BookOpen,
              title: 'Onboarding takes weeks',
              before: 'New employees spend weeks reading through policy documents and past projects',
              after: 'Ask questions from day one — knowledge base answers everything instantly'
            },
            {
              icon: Lock,
              title: 'Compliance nightmares',
              before: 'Using cloud AI tools violates HIPAA, GDPR, and internal data policies',
              after: 'Fully compliant — data stays on-premise, no third party ever touches it'
            }
          ].map(item => (
            <div key={item.title} className="bg-[#1c1c1e] rounded-2xl p-5 border border-[#2a2a2a]">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-9 h-9 bg-[#1e1b4b] rounded-xl flex items-center justify-center flex-shrink-0">
                  <item.icon size={18} color="#7C75D4" />
                </div>
                <h3 className="text-sm font-semibold text-white">{item.title}</h3>
              </div>
              <p className="text-xs text-red-400 flex items-start gap-1.5 mb-2"><span>✗</span>{item.before}</p>
              <p className="text-xs text-green-400 flex items-start gap-1.5"><span>✓</span>{item.after}</p>
            </div>
          ))}
        </div>
      </section>


      <section className="py-14 border-b border-[#3a3a3c]">
        <p className="text-lg font-bold text-white uppercase tracking-widest mb-6">Why self-hosted</p>
        <div className="grid grid-cols-2 gap-4 w-full">
          {[
            { icon: Lock, title: '100% private', desc: 'Data never leaves your server. Not even to us. Runs fully on your own infrastructure.' },
            { icon: Building, title: 'For any industry', desc: 'Hospitals, law firms, banks, government — any organisation with confidential documents.' },
            { icon: Users, title: 'Multi-user with roles', desc: 'Each employee sees only their own documents. Admin controls access for the whole team.' },
            { icon: Cpu, title: 'Local AI — no API keys', desc: 'Runs with open source LLMs like Llama 3 on your own hardware. No external API calls.' }
          ].map(b => (
            <div key={b.title} className="flex items-start gap-3 bg-[#1c1c1e] border border-[#2a2a2a] rounded-2xl p-5">
              <div className="w-9 h-9 bg-[#1e1b4b] rounded-xl flex items-center justify-center flex-shrink-0">
                <b.icon size={18} color="#7C75D4" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white mb-1">{b.title}</h3>
                <p className="text-xs text-[#999] leading-relaxed">{b.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>


      <section className="py-14 border-b border-[#3a3a3c]">
        <p className="text-xs font-medium text-[#666] uppercase tracking-widest mb-2">Built for these industries</p>
        <h2 className="text-2xl font-semibold text-white mb-8">Any industry with sensitive documents</h2>
        <div className="grid grid-cols-3 gap-4 w-full">
          {[
            { icon: '🏥', title: 'Healthcare', desc: 'Search patient histories, drug interactions, and clinical guidelines — privately on your hospital server' },
            { icon: '⚖️', title: 'Legal', desc: 'Search across thousands of case files, contracts, and legal precedents instantly' },
            { icon: '🏦', title: 'Finance & Banking', desc: 'Internal policy search, compliance docs, and audit trails — all private' },
            { icon: '🏛️', title: 'Government', desc: 'Classified document search, policy management, and inter-department knowledge sharing' },
            { icon: '🎓', title: 'Education', desc: 'University research databases, student records, and academic knowledge management' },
            { icon: '🏭', title: 'Manufacturing', desc: 'Technical manuals, quality standards, and production documentation search' },
            { icon: '💊', title: 'Pharmaceuticals', desc: 'Drug research papers, clinical trial data, and regulatory compliance documents' },
            { icon: '🛡️', title: 'Insurance', desc: 'Policy documents, claims history, and risk assessment knowledge bases' },
            { icon: '🔬', title: 'Research & Science', desc: 'Academic papers, lab notes, and research findings across your entire organisation' }
          ].map(ind => (
            <div key={ind.title} className="bg-[#1c1c1e] border border-[#2a2a2a] rounded-2xl p-5">
              <div className="text-2xl mb-3">{ind.icon}</div>
              <h3 className="text-sm font-semibold text-white mb-1">{ind.title}</h3>
              <p className="text-xs text-[#999] leading-relaxed">{ind.desc}</p>
            </div>
          ))}
        </div>
      </section>

 
      <section className="py-14">
        <div className="max-w-xl">
          <h2 className="text-2xl font-semibold text-white mb-1">Interested? Let's talk.</h2>
          <p className="text-sm text-[#999] mb-8">Fill in your details and our team will reach out within 24 hours.</p>

          {submitted ? (
            <div className="bg-[#1c1c1e] border border-green-800 rounded-2xl p-6">
              <h3 className="text-sm font-semibold text-green-400 mb-1">Message sent ✓</h3>
              <p className="text-xs text-[#999]">We'll reach out within 24 hours.</p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Your name"
                  placeholder="Shubhrato Badole"
                  value={form.name}
                  onChange={e => setForm({ ...form, name: e.target.value })}
                />
                <Input
                  label="Company name"
                  placeholder="Acme Corp"
                  value={form.company}
                  onChange={e => setForm({ ...form, company: e.target.value })}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Work email"
                  type="email"
                  placeholder="you@company.com"
                  value={form.email}
                  onChange={e => setForm({ ...form, email: e.target.value })}
                />
                <Input
                  label="Team size"
                  placeholder="e.g. 50–200"
                  value={form.teamSize}
                  onChange={e => setForm({ ...form, teamSize: e.target.value })}
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-xs text-[#aaa]">What are you trying to solve?</label>
                <textarea
                  value={form.message}
                  onChange={e => setForm({ ...form, message: e.target.value })}
                  placeholder="e.g. We want our legal team to search across 10,000 case files privately..."
                  rows={4}
                  className="bg-[#2a2a2e] border border-[#3a3a3a] rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-[#534AB7] transition-colors placeholder:text-[#555] resize-none"
                />
              </div>
              <div className="flex gap-3">
                <Button type="submit" className="px-8">
                  Send message
                </Button>
                <Link to="/">
                  <Button variant="ghost">
                    Back to home
                  </Button>
                </Link>
              </div>
            </form>
          )}
        </div>
      </section>
      </div>

      {/* Footer */}
      <footer className="px-8 py-6 border-t border-[#3a3a3c] flex items-center justify-between mt-auto">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 bg-[#534AB7] rounded-md flex items-center justify-center">
            <Brain size={13} color="white" fill="white" />
          </div>
          <span className="text-xs text-[#666]">ResearchMind AI</span>
        </div>
        <p className="text-xs text-[#666]">Built by Shubhrato Badole</p>
      </footer>
    </div>
  )
}