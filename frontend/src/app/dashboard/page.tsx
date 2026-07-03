"use client";
import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { fetchSummary, fetchStatements, type Summary, type Statement } from "@/lib/api";
import SpendingChart from "@/components/spending-chart";

export default function DashboardPage() {
  const { getToken } = useAuth();
  const [summary, setSummary] = useState<Summary | null>(null);
  const [statements, setStatements] = useState<Statement[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const token = await getToken();
      if (!token) return;
      try {
        const [s, stmts] = await Promise.all([fetchSummary(token), fetchStatements(token)]);
        setSummary(s);
        setStatements(stmts);
      } finally {
        setLoading(false);
      }
    })();
  }, [getToken]);

  if (loading) {
    return <div className="p-8 text-gray-400 text-sm">Loading...</div>;
  }

  const hasData = summary && (summary.by_category.length > 0 || summary.by_month.length > 0);

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <h2 className="text-2xl font-bold mb-6">Overview</h2>

      {!hasData ? (
        <div className="text-center py-20 text-gray-400">
          <p className="text-lg mb-2">No data yet</p>
          <p className="text-sm">
            <a href="/dashboard/upload" className="text-indigo-600 hover:underline">Upload a bank statement</a> to get started.
          </p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-3 gap-4 mb-8">
            <StatCard label="Total Spent" value={`$${Number(summary.total_spent).toFixed(2)}`} />
            <StatCard label="Statements" value={String(statements.length)} />
            <StatCard label="Categories" value={String(summary.by_category.length)} />
          </div>

          <div className="grid grid-cols-2 gap-6 mb-8">
            <ChartCard title="Spending by Category">
              <SpendingChart data={summary.by_category} type="pie" />
            </ChartCard>
            <ChartCard title="Monthly Trend">
              <SpendingChart data={summary.by_month} type="bar" />
            </ChartCard>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-4">Top Merchants</h3>
            <div className="space-y-2">
              {summary.top_merchants.map((m) => (
                <div key={m.name} className="flex justify-between items-center text-sm">
                  <span className="text-gray-700 truncate max-w-sm">{m.name}</span>
                  <span className="font-semibold text-gray-900 ml-4">${m.total.toFixed(2)}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-4">{title}</h3>
      {children}
    </div>
  );
}
