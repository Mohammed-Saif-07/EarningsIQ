type Props = { rows: Array<Record<string, unknown>> };

export default function SignalLeaderboard({ rows }: Props) {
  return (
    <section className="bg-white p-5 shadow-sm">
      <h2 className="mb-4 text-lg font-semibold">Signal Leaderboard</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-slate-500">
            <tr><th>Ticker</th><th>Signal</th><th>Confidence</th><th>1D</th><th>5D</th><th>Anomalies</th></tr>
          </thead>
          <tbody>
            {rows.length === 0 && (
              <tr className="border-t border-slate-100">
                <td className="py-3 text-slate-500" colSpan={6}>Loading signal leaderboard...</td>
              </tr>
            )}
            {rows.map((row) => (
              <tr key={String(row.ticker)} className="border-t border-slate-100">
                <td className="py-3 font-semibold">{String(row.ticker)}</td>
                <td>{String(row.signal)}</td>
                <td>{String(row.confidence)}</td>
                <td>{String(row.price_delta_1d)}%</td>
                <td>{String(row.price_delta_5d)}%</td>
                <td>{String(row.anomalies)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
