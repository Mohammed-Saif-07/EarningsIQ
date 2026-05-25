import { useEffect, useState } from "react";
import { api } from "../lib/api";
import AgentStatusPanel from "./AgentStatusPanel";
import AnomalyCard from "./AnomalyCard";
import QABox from "./QABox";
import SentimentTimeline from "./SentimentTimeline";
import SignalLeaderboard from "./SignalLeaderboard";
import TranscriptViewer from "./TranscriptViewer";

export default function Dashboard() {
  const [ticker, setTicker] = useState("AAPL");
  const [signals, setSignals] = useState<Array<Record<string, unknown>>>([]);
  const [sentiment, setSentiment] = useState<Array<{ index: number; score: number }>>([]);
  const [signal, setSignal] = useState<Record<string, unknown>>({ anomalies: [] });
  const [transcript, setTranscript] = useState<string[]>([]);
  const [signalLoading, setSignalLoading] = useState(true);

  useEffect(() => {
    api.signals().then(setSignals).catch(() => setSignals([]));
  }, []);

  useEffect(() => {
    setSignalLoading(true);
    api.sentiment(ticker).then((row) => setSentiment((row.timeline as Array<{ index: number; score: number }>) || []));
    api.signal(ticker).then(setSignal).finally(() => setSignalLoading(false));
    api.transcript(ticker).then((row) => setTranscript((row.chunks as string[]) || []));
  }, [ticker]);

  return (
    <main>
      <section className="bg-ink px-6 py-7 text-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold">EarningsIQ</h1>
            <p className="mt-1 text-slate-200">What CFOs say, what the market misses.</p>
          </div>
          <select className="w-36 bg-white px-3 py-2 text-ink" value={ticker} onChange={(event) => setTicker(event.target.value)}>
            {["AAPL", "MSFT", "NVDA", "TSLA", "JPM"].map((value) => <option key={value}>{value}</option>)}
          </select>
        </div>
      </section>
      <div className="mx-auto grid max-w-7xl gap-5 px-6 py-6">
        <AgentStatusPanel />
        <div className="grid gap-5 lg:grid-cols-2">
          <SentimentTimeline data={sentiment} />
          <AnomalyCard anomalies={(signal.anomalies as Array<Record<string, unknown>>) || []} loading={signalLoading} />
        </div>
        <SignalLeaderboard rows={signals} />
        <div className="grid gap-5 lg:grid-cols-2">
          <TranscriptViewer chunks={transcript} />
          <QABox ticker={ticker} />
        </div>
      </div>
    </main>
  );
}
