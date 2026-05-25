import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

type Props = { data: Array<{ index: number; score: number }> };

export default function SentimentTimeline({ data }: Props) {
  return (
    <section className="bg-white p-5 shadow-sm">
      <h2 className="mb-4 text-lg font-semibold">Sentiment Timeline</h2>
      <div className="h-56">
        {data.length === 0 && <p className="text-sm text-slate-500">Loading sentiment timeline...</p>}
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <XAxis dataKey="index" />
            <YAxis domain={[-1, 1]} />
            <Tooltip />
            <Line type="monotone" dataKey="score" stroke="#126c7a" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
