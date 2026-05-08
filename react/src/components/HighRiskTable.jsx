export default function HighRiskTable({ customers, title = "High-Risk Customers", eyebrow = "Action List" }) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h2>{title}</h2>
        </div>
      </div>
      {!customers?.length ? (
        <div className="empty-state">
          <p>Chua co khach hang nao trong danh sach nay.</p>
        </div>
      ) : (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Customer</th>
                <th>Contract</th>
                <th>Internet</th>
                <th>Payment</th>
                <th>Label</th>
                <th>Probability</th>
              </tr>
            </thead>
            <tbody>
              {customers.map((customer, index) => (
                <tr key={`${customer.customerId}-${index}`}>
                  <td>{customer.customerId || "-"}</td>
                  <td>{customer.contract || "-"}</td>
                  <td>{customer.internetService || "-"}</td>
                  <td>{customer.paymentMethod || "-"}</td>
                  <td>{customer.predictedChurn}</td>
                  <td>{(customer.churnProbability * 100).toFixed(2)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
