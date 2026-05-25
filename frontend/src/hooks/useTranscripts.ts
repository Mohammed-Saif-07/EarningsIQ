import { useEffect, useState } from "react";
import { api } from "../lib/api";

export function useTranscripts() {
  const [rows, setRows] = useState<Array<Record<string, unknown>>>([]);
  useEffect(() => {
    api.transcripts().then(setRows).catch(() => setRows([]));
  }, []);
  return rows;
}
