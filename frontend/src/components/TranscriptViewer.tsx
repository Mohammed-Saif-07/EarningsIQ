type Props = { chunks: string[] };

export default function TranscriptViewer({ chunks }: Props) {
  return (
    <section className="bg-white p-5 shadow-sm">
      <h2 className="mb-4 text-lg font-semibold">Transcript Viewer</h2>
      <div className="max-h-72 space-y-3 overflow-y-auto pr-2 text-sm leading-6">
        {chunks.length === 0 && <p className="text-slate-500">Loading transcript chunks...</p>}
        {chunks.map((chunk, index) => (
          <p key={index}><span className="mr-2 font-semibold text-accent">{index + 1}</span>{chunk}</p>
        ))}
      </div>
    </section>
  );
}
