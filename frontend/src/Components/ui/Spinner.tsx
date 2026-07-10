interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg'
}

export default function Spinner({ size = 'md' }: SpinnerProps) {
  const sizes = { sm: 'w-4 h-4', md: 'w-6 h-6', lg: 'w-8 h-8' }
  return (
    <div className={`${sizes[size]} border-2 border-gray-200 border-t-[#534AB7] rounded-full animate-spin`} />
  )

}