import { Activity } from "lucide-react";
import { useWebSocket } from "../hooks/useWebSocket";

export default function AgentStatusPanel() {
  const message = useWebSocket();
  const agents = (message?.agents as Array<Record<string, unknown>> | undefined) || [];
  return (
    <section className="bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center gap-2">
        <Activity className="h-5 w-5 text-accent" />
        <h2 className="text-lg font-semibold">K8s Agent Pods</h2>
      </div>
      <div className="grid gap-2 sm:grid-cols-5">
        {agents.map((agent) => (
          <div key={String(agent.name)} className="border border-slate-200 p-3">
            <div className="font-semibold">{String(agent.name)}</div>
            <div className="text-sm text-slate-500">{String(agent.status)} · {String(agent.pods)} pod</div>
          </div>
        ))}
      </div>
    </section>
  );
}
