import { useState, useRef, useEffect } from 'react'
import { FileText, Globe, Layers, ChevronDown } from 'lucide-react'

export type SearchMode = 'docs' | 'docs_web' | 'web'

const OPTIONS: { value: SearchMode; label: string; icon: typeof FileText }[] = [
  { value: 'docs', label: 'My docs only', icon: FileText },
  { value: 'docs_web', label: 'Docs + web', icon: Layers },
  { value: 'web', label: 'Web only', icon: Globe }
]

export default function SearchModeDropdown({
  value,
  onChange
}: {
  value: SearchMode
  onChange: (mode: SearchMode) => void
}) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const current = OPTIONS.find(o => o.value === value) ?? OPTIONS[1]
  const Icon = current.icon

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(prev => !prev)}
        className="flex items-center gap-2 border border-[#3a3a3c] rounded-full px-3 py-1.5 text-xs text-white bg-[#1c1c1e] hover:border-[#534AB7] transition-colors"
      >
        <Icon size={13} className="text-[#7C75D4]" />
        {current.label}
        <ChevronDown size={12} className="text-[#888]" />
      </button>
      {open && (
        <div className="absolute right-0 top-9 bg-[#1c1c1e] border border-[#3a3a3c] rounded-lg p-1 w-40 z-10">
          {OPTIONS.map(opt => {
            const OptIcon = opt.icon
            const isActive = opt.value === value
            return (
              <button
                key={opt.value}
                onClick={() => { onChange(opt.value); setOpen(false) }}
                className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-xs transition-colors ${
                  isActive ? 'bg-[#1e1b4b] text-[#7C75D4]' : 'text-[#ccc] hover:bg-[#2d2d2f]'
                }`}
              >
                <OptIcon size={13} />
                {opt.label}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}