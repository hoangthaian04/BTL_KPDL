export default function MetricCard({ label, value, accent }) {
  return (
    <article className="metric-card">
      <span className="metric-accent" style={{ background: accent }} />
      <p className="metric-label">{label}</p>
      <h3 className="metric-value">{value}</h3>
    </article>
  );
}
