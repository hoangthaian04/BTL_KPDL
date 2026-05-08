function buildGradient(segments) {
  const total = segments.reduce((sum, segment) => sum + segment.value, 0) || 1;
  let start = 0;
  return segments
    .map((segment) => {
      const percentage = (segment.value / total) * 100;
      const stop = `${segment.color} ${start}% ${start + percentage}%`;
      start += percentage;
      return stop;
    })
    .join(", ");
}

export default function PieChart({ title, segments }) {
  const total = segments.reduce((sum, segment) => sum + segment.value, 0) || 1;

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Distribution</p>
          <h2>{title}</h2>
        </div>
      </div>

      <div className="donut-layout">
        <div className="donut-stage">
          <div
            className="single-donut"
            style={{ background: `conic-gradient(${buildGradient(segments)})` }}
          />
          <div className="single-donut-core">
            <span>Total</span>
            <strong>{total}</strong>
            <small>customers</small>
          </div>
        </div>

        <div className="nested-donut-legend">
          <div className="legend-group">
            <h3>Churn Breakdown</h3>
            {segments.map((segment) => (
              <div className="pie-legend-item" key={segment.key}>
                <span className="pie-color" style={{ background: segment.color }} />
                <span>{segment.label}</span>
                <strong>{segment.value}</strong>
                <em>{((segment.value / total) * 100).toFixed(1)}%</em>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
