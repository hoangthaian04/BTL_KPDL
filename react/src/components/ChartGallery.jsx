const chartOrder = [
  "churn_distribution",
  "model_comparison_f1",
  "confusion_matrix",
  "feature_importance"
];

export default function ChartGallery({ charts }) {
  if (!charts?.length) {
    return null;
  }

  const orderedCharts = [...charts].sort((left, right) => {
    const leftIndex = chartOrder.indexOf(left.key);
    const rightIndex = chartOrder.indexOf(right.key);
    return (leftIndex === -1 ? 99 : leftIndex) - (rightIndex === -1 ? 99 : rightIndex);
  });

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Artifacts</p>
          <h2>Training Charts</h2>
        </div>
      </div>
      <div className="gallery-grid gallery-grid-balanced">
        {orderedCharts.map((chart) => (
          <article
            className={`gallery-card ${chart.key === "feature_importance" ? "gallery-card-wide" : ""}`}
            key={chart.key}
          >
            <div className="gallery-card-header">
              <h3>{chart.title}</h3>
              <span className="gallery-chip">Model artifact</span>
            </div>
            <img src={chart.imagePath} alt={chart.title} />
          </article>
        ))}
      </div>
    </section>
  );
}
