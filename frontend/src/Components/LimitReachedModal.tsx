import Modal from './ui/Modal'
import UpgradeButton from './UpgradeButton'

interface Props {
  open: boolean
  onClose: () => void
  message: string
}

export default function LimitReachedModal({ open, onClose, message }: Props) {
  return (
    <Modal open={open} onClose={onClose} title="Limit reached">
      <div className="flex flex-col gap-4">
        <p className="text-sm text-[#ccc] leading-relaxed">{message}</p>
        <UpgradeButton />
        <button
          onClick={onClose}
          className="text-xs text-[#666] hover:text-white transition-colors"
        >
          Maybe later
        </button>
      </div>
    </Modal>
  )
}