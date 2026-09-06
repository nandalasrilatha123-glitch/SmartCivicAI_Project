export default function ChartCard({ title, subtitle, children, className = "" }) {
  return (
    <div className={`bg-paper-raised border border-ink/10 p-5 ${className}`}>
      <h3 className="font-display text-base font-semibold text-ink">{title}</h3>
      {subtitle && <p className="text-xs text-ink-faint mt-0.5 mb-3">{subtitle}</p>}
      <div className={subtitle ? "" : "mt-3"}>{children}</div>
    </div>
  );
}
