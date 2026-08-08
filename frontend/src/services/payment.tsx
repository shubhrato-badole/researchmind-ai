import client from '../Api/client'

const RAZORPAY_KEY_ID = import.meta.env.VITE_RAZORPAY_KEY_ID

export async function startUpgrade(onSuccess: () => void, onError: (msg: string) => void) {
  try {
    const orderRes = await client.post('/payment/create-order')
    const { order_id, amount, currency } = orderRes.data

    const options = {
      key: RAZORPAY_KEY_ID,
      amount,
      currency,
      name: 'ResearchMind',
      description: 'Upgrade to Pro',
      order_id,
      handler: async function (response: any) {
        try {
          await client.post('/payment/verify', {
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature
          })
          onSuccess()
        } catch (err) {
          onError('Payment succeeded but verification failed. Contact support.')
        }
      },
      theme: { color: '#534AB7' },
      modal: {
        ondismiss: function () {
          onError('Payment cancelled')
        }
      }
    }

    const rzp = new (window as any).Razorpay(options)
    rzp.open()
  } catch (err: any) {
    onError(err.response?.data?.detail || 'Failed to start payment')
  }
}