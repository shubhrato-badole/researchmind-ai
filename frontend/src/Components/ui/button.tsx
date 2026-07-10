
interface ButtonProps {
  children: React.ReactNode
  onClick?: () => void
  variant?: 'primary' | 'ghost' | 'danger' | 'success'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  className?: string
  type?: 'button' | 'submit' | 'reset'
}

export default function Button({
  children, 
  onClick, 
  variant = 'primary',
  size = 'md',
  disabled,
  className,
  type,
}:ButtonProps){
  const base = `inline-flex items-center justify-center gap-2 font-medium rounded-lg 
                transition-all cursor-pointer border`

   const variants = {
    primary: 'bg-[#534AB7] text-white border-[#534AB7] hover:bg-[#3C3489]',
    ghost: 'bg-[#2a2a2e] text-white border-[#3a3a3a] hover:bg-[#333]',
    danger: 'bg-red-500 text-white border-red-500 hover:bg-red-600',
    success: 'bg-green-500 text-white border-green-500 hover:bg-green-600'
  }

  const sizes = {
    sm: 'text-xs px-3 py-1.5',
    md: 'text-sm px-4 py-3',
    lg: 'text-base px-6 py-3'
  }

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${base} ${variants[variant]} ${sizes[size]} ${disabled ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}
    >
      {children}
    </button>
  )
}