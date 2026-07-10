interface ModalProps {
  open: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
}



export default function Modal({ open, onClose, title, children }: ModalProps) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-[#1c1c1e] border border-[#3a3a3c] rounded-2xl shadow-xl p-6 w-full max-w-md mx-4 z-10">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-white">{title}</h3>
          <button onClick={onClose} className="text-[#666] hover:text-white text-lg transition-colors">×</button>
        </div>
        {children}
      </div>
    </div>
  )
}