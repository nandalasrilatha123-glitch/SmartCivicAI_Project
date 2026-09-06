export default function StatCard({ label, value, accent = false }) {
  return (
    <div className={`border p-4 ${accent ? "border-marigold-dark bg-marigold/10" : "border-ink/10 bg-paper-raised"}`}>
      <p className="text-xs text-ink-faint mb-1">{label}</p>
      <p className="font-display text-2xl font-semibold text-ink">{value}</p>
    </div>
  );
}
