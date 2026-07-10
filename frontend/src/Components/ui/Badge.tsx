interface BadgeProps {
  children: React.ReactNode
  color?: 'purple' | 'green' | 'red' | 'amber' | 'gray'
}

export default function Badge({ children, color = 'purple' }: BadgeProps) {
 
  const colors = {
    purple: 'bg-[#EEEDFE] text-[#3C3489]',
    green: 'bg-green-50 text-green-700',
    red: 'bg-red-50 text-red-700',
    amber: 'bg-amber-50 text-amber-700',
    gray: 'bg-gray-100 text-gray-600'
  }
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${colors[color]}`}>
      {children}
    </span>
  )


}