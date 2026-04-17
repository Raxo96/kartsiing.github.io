export default function StatCard({ label, value, sub, accent }) {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-lg px-5 py-4 flex flex-col gap-1">
      <span className="text-xs text-zinc-500 uppercase tracking-wider">{label}</span>
      <span className={`text-2xl font-bold ${accent ?? 'text-zinc-100'}`}>{value}</span>
      {sub && <span className="text-xs text-zinc-400">{sub}</span>}
    </div>
  )
}
