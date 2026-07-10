

interface CardProps {
  children: React.ReactNode
  className?: string
}



export default function Card({ children, className = '' }:CardProps) {
  return (
    <div className={`bg-white border border-gray-100 rounded-xl p-4 ${className}`}>
      {children}
    </div>
  )
}