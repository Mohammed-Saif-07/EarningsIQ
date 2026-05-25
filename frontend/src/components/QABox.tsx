import { Send } from "lucide-react";
import { useState } from "react";
import { api } from "../lib/api";

type Props = { ticker: string };

export default function QABox({ ticker }: Props) {
  const [question, setQuestion] = useState("What did the CFO say about margins?");
  const [answer, setAnswer] = useState("");
  const ask = async () => {
    const response = await api.ask(ticker, question);
    setAnswer(String(response.answer || ""));
  };
  return (
    <section className="bg-white p-5 shadow-sm">
      <h2 className="mb-4 text-lg font-semibold">Q&A</h2>
      <div className="flex gap-2">
        <input className="min-w-0 flex-1 border border-slate-300 px-3 py-2" value={question} onChange={(event) => setQuestion(event.target.value)} />
        <button className="bg-accent px-3 py-2 text-white" onClick={ask} aria-label="Ask"><Send className="h-4 w-4" /></button>
      </div>
      {answer && <p className="mt-4 text-sm leading-6">{answer}</p>}
    </section>
  );
}
