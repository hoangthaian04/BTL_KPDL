export default function BarChart({ title, items, valueKey, labelKey, color = "#2a9d8f", maxValue = null, formatter }) {
  const safeMax = maxValue ?? Math.max(...items.map((item) => item[valueKey] || 0), 1);

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Chart</p>
          <h2>{title}</h2>
        </div>
      </div>
      <div className="bar-chart">
        {items.map((item) => {
          const rawValue = item[valueKey] || 0;
          const width = `${(rawValue / safeMax) * 100}%`;
          return (
            <div className="bar-row" key={item[labelKey]}>
              <div className="bar-row-header">
                <span>{item[labelKey]}</span>
                <strong>{formatter ? formatter(rawValue) : rawValue}</strong>
              </div>
              <div className="bar-track">
                <div className="bar-fill" style={{ width, background: color }} />
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
