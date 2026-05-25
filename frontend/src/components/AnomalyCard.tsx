import { AlertTriangle } from "lucide-react";

type Props = { anomalies: Array<Record<string, unknown>>; loading?: boolean };

export default function AnomalyCard({ anomalies, loading = false }: Props) {
  return (
    <section className="bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center gap-2">
        <AlertTriangle className="h-5 w-5 text-signal" />
        <h2 className="text-lg font-semibold">Anomalies</h2>
      </div>
      <div className="space-y-3">
        {loading && anomalies.length === 0 && (
          <p className="text-sm text-slate-500">Loading anomaly signals from the API...</p>
        )}
        {!loading && anomalies.length === 0 && (
          <p className="text-sm text-slate-500">No anomalies found for this filing.</p>
        )}
        {anomalies.map((item, index) => (
          <article key={index} className="border-l-4 border-signal bg-orange-50 p-3">
            <div className="text-xs uppercase tracking-wide text-slate-500">{String(item.severity)} · z={String(item.zscore)}</div>
            <p className="mt-1 text-sm">{String(item.sentence_text)}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
