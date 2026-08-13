import { Link } from 'react-router-dom'
import { Brain } from 'lucide-react'
import { Upload, Mic, GraduationCap, Map, BookOpen, Briefcase } from 'lucide-react'

export default function Landing() {
    return(
         <div className="min-h-screen bg-[#2d2d2f] flex flex-col w-full">

        {/* Nav content now shares the same max-w-5xl/px-8 wrapper as everything else,
            so the logo lines up with the section content below it at every screen size. */}
        <nav className='sticky top-0 z-10 bg-[#2d2d2f] border-b border-[#3a3a3c]'>
          <div className="max-w-5xl mx-auto px-8 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 bg-[#534AB7] rounded-xl flex items-center justify-center">
                <Brain size={20} color="white" />
              </div>
              <span className="text-lg font-semibold text-white">ResearchMind</span>
            </div>
            <div className="flex items-center gap-4">
              <Link to="/enterprise" className="text-sm text-[white] border border-[#555] px-4 py-2 rounded-lg hover:text-white hover:border-[#888] transition-colors">
                Enterprise
              </Link>
              <Link to="/login" className="text-sm text-[white] border border-[#555] px-4 py-2 rounded-lg hover:text-white hover:border-[#888] transition-colors">
                Sign in
              </Link>
              <Link to="/register" className="text-sm bg-[#534AB7] text-white px-4 py-2 rounded-lg hover:bg-[#3C3489] transition-colors">
                Get started free
              </Link>
            </div>
          </div>
        </nav>

        <div className="max-w-5xl mx-auto w-full px-8 flex flex-col">

          {/* Hero — fixed the stray quote in the className, unified vertical rhythm to pt-24/pb-16 */}
          <section className="flex flex-col items-center text-center pt-24 pb-16">
            <div className="inline-flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-full bg-[#EEEDFE] text-[#3C3489] border border-[#AFA9EC] mb-6">
              <Brain size={16} color="#7C75D4" fill="#7C75D4" />
              AI-powered knowledge base
            </div>
            <h1 className="text-4xl font-semibold text-white leading-tight max-w-xl mb-4">
              Your documents.<br />
              <span className="text-[#534AB7]">Answered instantly.</span>
            </h1>
            <p className="text-base text-[#999] max-w-md leading-relaxed mb-8">
              Upload PDFs, websites, and YouTube videos. Ask any question. Get answers from your own content — with sources shown.
            </p>

            <div className="flex gap-3 mb-4">
              <Link to="/register" className="bg-[#534AB7] text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-[#3C3489] transition-colors">
                Get started free
              </Link>
              <Link to="/enterprise" className="border border-[#555] text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:border-[#888] transition-colors">
                For enterprises →
              </Link>
            </div>

            <p className="text-xs text-[#666] mt-3">No credit card required · Free to start</p>
          </section>

          {/* Three steps — dropped the ml-11 hack, eyebrow now aligns naturally with the cards */}
          <section className="py-20 border-b border-[#3a3a3c]">
            <p className="text-xs font-medium text-[#666] uppercase tracking-widest mb-2">How it works</p>
            <h2 className="text-xl font-semibold text-white mb-2">Three steps. That's it</h2>
            <p className="text-sm text-[#999] mb-8">No setup. No configuration. Just upload and start asking questions.</p>

            <div className="grid grid-cols-3 gap-5">
              {[
                { num: '1', title: 'Add your content', desc: 'Upload a PDF, paste a website URL, or drop a YouTube link. We handle the rest.' },
                { num: '2', title: 'Ask anything', desc: 'Type or speak your question. Search only your documents, or include the web too.' },
                { num: '3', title: 'Get cited answers', desc: 'Every answer shows exactly which document it came from. No guessing.' }
              ].map(step => (
                <div key={step.num} className="bg-[#1c1c1e] rounded-2xl p-6">
                  <div className="w-8 h-8 bg-[#534AB7] text-white rounded-full flex items-center justify-center text-sm font-medium mb-4">{step.num}</div>
                  <h3 className="text-base font-semibold text-white mb-2">{step.title}</h3>
                  <p className="text-sm text-[#999] leading-relaxed">{step.desc}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Why ResearchMind — vertical rhythm matched to py-20 */}
          <section className="py-20 border-b border-[#3a3a3c]">
            <p className="text-xs font-medium text-[#666] uppercase tracking-widest text-center mb-2">Why ResearchMind</p>
            <h2 className="text-xl font-semibold text-white text-center mb-2">You already have the knowledge.<br />You just can't find it fast enough.</h2>
            <p className="text-sm text-[#999] text-center max-w-md mx-auto mb-8">You save PDFs you never re-read. You watch YouTube videos and forget them the next day. ResearchMind fixes all of that.</p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-3xl mx-auto mb-10">
              {[
                { icon: '📄', title: 'Saved PDFs you never use', before: 'You download research papers and never open them again', after: 'Upload once, ask questions from them forever' },
                { icon: '▶️', title: 'Videos you forget instantly', before: 'You watch a 2-hour tutorial and remember nothing a week later', after: 'Add the video, quiz yourself on it anytime' },
                { icon: '🔖', title: 'Bookmarks nobody opens', before: '200 saved articles you\'ll "read later" but never do', after: 'Add the URL, search across all of them in seconds' },
                { icon: '🔍', title: 'Ctrl+F is not enough', before: 'You search for "authentication" but the doc says "login flow"', after: 'AI understands meaning — finds it even with different words' }
              ].map(item => (
                <div key={item.title} className="bg-[#3a3a3c] rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-8 h-8 bg-[#2d2d2f] rounded-lg flex items-center justify-center text-base border border-[#555]">{item.icon}</div>
                    <h3 className="text-sm font-semibold text-white">{item.title}</h3>
                  </div>
                  <p className="text-xs text-red-400 flex items-start gap-1.5 mb-1.5"><span>✗</span>{item.before}</p>
                  <p className="text-xs text-green-400 flex items-start gap-1.5"><span>✓</span>{item.after}</p>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-3xl mx-auto">
              {[
                { text: 'I uploaded all my RAG study material and used it to prep for my AI engineer interview. Got the job.', author: 'CS student, Nagpur' },
                { text: 'I paste YouTube links of lectures and ask questions instead of rewatching 2-hour videos before exams.', author: 'Engineering student' },
                { text: 'I add research papers and ask it to explain the methodology. Saves me hours every week.', author: 'PhD researcher' }
              ].map((t, i) => (
                <div key={i} className="border border-[#3a3a3c] rounded-xl p-4">
                  <p className="text-xs text-[#999] leading-relaxed italic mb-3">"{t.text}"</p>
                  <p className="text-xs text-[#666]">{t.author}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Built for people — dropped the extra px-12 (was stacking on top of the parent's px-8,
              which is why this heading sat further right than "Three steps" above it) */}
          <section className="py-20">
            <p className="text-xs font-medium text-[#666] uppercase tracking-widest mb-2">For individuals</p>
            <h2 className="text-2xl font-semibold text-white mb-2">Built for people who learn and research</h2>
            <p className="text-sm text-[#999] mb-6">Students, researchers, developers — anyone tired of searching through their own files manually.</p>

            <div className="grid grid-cols-2 gap-4 w-full">
              {[
                { icon: Upload, title: 'Upload anything', desc: 'PDF, website, YouTube video, or a photo of handwritten notes' },
                { icon: Mic, title: 'Voice search', desc: 'Ask questions by speaking — no typing needed' },
                { icon: GraduationCap, title: 'Auto quiz', desc: 'AI generates quiz questions from your documents to test what you know' },
                { icon: Map, title: 'Learning roadmap', desc: 'Tell us what you want to learn — we build a step by step path and fill your knowledge base' },
                { icon: BookOpen, title: 'Flashcards', desc: 'Generate flashcards from your content for active recall' },
                { icon: Briefcase, title: 'Interview mode', desc: 'Practice with open-ended questions and get AI feedback' }
              ].map(feat => (
                <div key={feat.title} className="flex items-start gap-4 bg-[#3a3a3c] rounded-2xl p-5 border border-[#2a2a2a]">
                  <div className="w-10 h-10 bg-[#1e1b4b] rounded-xl flex items-center justify-center flex-shrink-0">
                    <feat.icon size={20} color="#7C75D4" />
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-white mb-1">{feat.title}</h3>
                    <p className="text-sm text-[#999] leading-relaxed">{feat.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Enterprise CTA — removed the extra mx-8, now shares the same left/right edge as every
              section above it instead of indenting further */}
          <section className="mb-16">
            <div className="bg-[#1c1c1e] border border-[#3a3a3c] rounded-xl p-6 flex items-center justify-between gap-6">
              <div>
                <h3 className="text-base font-semibold text-white mb-1">Need this for your company?</h3>
                <p className="text-sm text-[#999] max-w-md">Run ResearchMind on your own server. Your data never leaves your building. Built for hospitals, law firms, and enterprises with strict data privacy requirements.</p>
              </div>
              <Link to="/enterprise" className="border border-[#534AB7] text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-[#534AB7] hover:text-white transition-colors whitespace-nowrap">
                Learn more →
              </Link>
            </div>
          </section>

        </div>

        {/* Footer content now shares the same max-w-5xl/px-8 wrapper too */}
        <footer className="border-t border-[#3a3a3c]">
          <div className="max-w-5xl mx-auto px-8 py-6 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 bg-[#534AB7] rounded-md flex items-center justify-center">
                <Brain size={12} color="white" />
              </div>
              <span className="text-xs text-[#666]">ResearchMind AI</span>
            </div>
            <div className="flex items-center gap-4 text-xs text-[#666]">
              <span>© 2026 ResearchMind AI</span>
              <a href="#" className="hover:text-white transition-colors">Privacy</a>
              <a href="#" className="hover:text-white transition-colors">Terms</a>
            </div>
          </div>
        </footer>

         </div>
    )
}