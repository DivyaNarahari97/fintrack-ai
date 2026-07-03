"use client";
import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { fetchTransactions, type TransactionPage } from "@/lib/api";
import TransactionTable from "@/components/transaction-table";

export default function TransactionsPage() {
  const { getToken } = useAuth();
  const [data, setData] = useState<TransactionPage | null>(null);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      const token = await getToken();
      if (!token || cancelled) return;
      const result = await fetchTransactions(token, {
        page,
        search: search || undefined,
        category: category || undefined,
      });
      if (!cancelled) { setData(result); setLoading(false); }
    })();
    return () => { cancelled = true; };
  }, [page, search, category, getToken]);

  const totalPages = data ? Math.ceil(data.total / data.page_size) : 1;

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <h2 className="text-2xl font-bold mb-6">Transactions</h2>
      <div className="flex gap-3 mb-5">
        <input
          type="text"
          placeholder="Search description..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
        />
        <input
          type="text"
          placeholder="Category"
          value={category}
          onChange={(e) => { setCategory(e.target.value); setPage(1); }}
          className="w-44 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
        />
      </div>

      {loading ? (
        <div className="text-sm text-gray-400 py-6">Loading...</div>
      ) : data ? (
        <>
          <TransactionTable transactions={data.items} />
          <div className="flex justify-between items-center mt-4 text-sm text-gray-500">
            <span>{data.total} transaction{data.total !== 1 ? "s" : ""}</span>
            <div className="flex items-center gap-2">
              <button
                disabled={page === 1}
                onClick={() => setPage((p) => p - 1)}
                className="px-3 py-1 border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50"
              >
                Prev
              </button>
              <span>
                {page} / {totalPages}
              </span>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                className="px-3 py-1 border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50"
              >
                Next
              </button>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}
