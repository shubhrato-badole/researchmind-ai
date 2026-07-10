interface input {
label?:string
type?:string
placeholder?:string
value:string
onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  error?: string
  className?: string
  labelClassName?: string

}


export default function Input ({
label,
type,
placeholder,
value,
onChange,
error,
className,
labelClassName
}:input){
return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label className={`text-[#aaa] ${labelClassName || 'text-xs'}`}>{label}</label>
      )}
      <input
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
       className={`bg-[#2a2a2e] border border-[#3a3a3a] rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-[#534AB7] transition-colors placeholder:text-[#555] ${error ? 'border-red-500' : ''} ${className}`}
      />
      {error && <span className="text-xs text-red-400">{error}</span>}
    </div>
  )
}