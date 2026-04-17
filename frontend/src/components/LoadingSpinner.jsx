export default function LoadingSpinner({ text = 'Loading…' }) {
  return (
    <div className="flex flex-col items-center justify-center py-24 gap-3 text-zinc-500">
      <div className="w-8 h-8 border-2 border-zinc-700 border-t-racing-red rounded-full animate-spin" />
      <span className="text-sm">{text}</span>
    </div>
  )
}
