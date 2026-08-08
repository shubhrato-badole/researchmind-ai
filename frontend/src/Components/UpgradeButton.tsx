import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import Button from './ui/button'
import { startUpgrade } from '../services/payment'

export default function UpgradeButton() {
  const queryClient = useQueryClient()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleUpgrade = () => {
    setError('')
    setLoading(true)
    startUpgrade(
      () => {
        setLoading(false)
        queryClient.invalidateQueries({ queryKey: ['user'] })
        alert('Welcome to Pro! All limits removed.')
      },
      (msg) => {
        setLoading(false)
        setError(msg)
      }
    )
  }

  return (
    <div>
      <Button onClick={handleUpgrade} disabled={loading}>
        {loading ? 'Opening checkout...' : 'Upgrade to Pro — ₹249/mo'}
      </Button>
      {error && <p className="text-xs text-red-400 mt-2">{error}</p>}
    </div>
  )
}