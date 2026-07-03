const API_BASE = "/api";

export type Statement = {
  id: string;
  filename: string;
  file_type: string;
  uploaded_at: string;
  status: string;
  error_message?: string;
};

export type Transaction = {
  id: string;
  statement_id: string;
  date: string;
  description: string;
  amount: number;
  currency: string;
  category?: string;
};

export type TransactionPage = {
  items: Transaction[];
  total: number;
  page: number;
  page_size: number;
};

export type CategoryTotal = {
  category: string;
  total: number;
  count: number;
};

export type MonthlyTotal = {
  month: string;
  total: number;
};

export type Summary = {
  by_category: CategoryTotal[];
  by_month: MonthlyTotal[];
  total_spent: number;
  top_merchants: { name: string; total: number; count: number }[];
};

async function apiFetch(path: string, token: string, init: RequestInit = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(init.headers as Record<string, string>),
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res;
}

export async function fetchStatements(token: string): Promise<Statement[]> {
  return (await apiFetch("/statements", token)).json();
}

export async function uploadStatement(
  token: string,
  file: File
): Promise<{ statement_id: string; status: string }> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/statements/upload`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function deleteStatement(token: string, id: string): Promise<void> {
  await apiFetch(`/statements/${id}`, token, { method: "DELETE", headers: {} });
}

export async function fetchTransactions(
  token: string,
  params?: { page?: number; page_size?: number; category?: string; search?: string }
): Promise<TransactionPage> {
  const q = new URLSearchParams();
  if (params?.page) q.set("page", String(params.page));
  if (params?.page_size) q.set("page_size", String(params.page_size));
  if (params?.category) q.set("category", params.category);
  if (params?.search) q.set("search", params.search);
  return (await apiFetch(`/transactions?${q}`, token)).json();
}

export async function fetchSummary(token: string): Promise<Summary> {
  return (await apiFetch("/transactions/summary", token)).json();
}

export async function streamChat(
  token: string,
  message: string,
  onChunk: (text: string) => void,
  onDone: () => void
): Promise<void> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ message }),
  });

  if (!res.ok) throw new Error(await res.text());
  if (!res.body) { onDone(); return; }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const data = line.slice(6);
      if (data === "[DONE]") {
        onDone();
        return;
      }
      try {
        const { text } = JSON.parse(data) as { text: string };
        onChunk(text);
      } catch {
        // malformed SSE chunk — skip
      }
    }
  }
  onDone();
}
