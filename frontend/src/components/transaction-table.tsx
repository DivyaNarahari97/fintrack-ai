import type { Transaction } from "@/lib/api";

const CATEGORY_COLORS: Record<string, string> = {
  "Food & Dining": "bg-orange-100 text-orange-700",
  "Transportation": "bg-blue-100 text-blue-700",
  "Shopping": "bg-pink-100 text-pink-700",
  "Entertainment": "bg-purple-100 text-purple-700",
  "Healthcare": "bg-green-100 text-green-700",
  "Education": "bg-yellow-100 text-yellow-700",
  "Utilities": "bg-gray-100 text-gray-600",
  "Housing": "bg-teal-100 text-teal-700",
  "Travel": "bg-sky-100 text-sky-700",
  "Income": "bg-emerald-100 text-emerald-700",
  "Transfers": "bg-slate-100 text-slate-600",
  "Other": "bg-gray-100 text-gray-500",
};

interface Props {
  transactions: Transaction[];
}

export default function TransactionTable({ transactions }: Props) {
  if (transactions.length === 0) {
    return <p className="text-sm text-gray-400 py-6 text-center">No transactions found.</p>;
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-gray-200">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-50 text-left border-b border-gray-200">
            <th className="px-4 py-3 font-medium text-gray-500 text-xs uppercase tracking-wide">Date</th>
            <th className="px-4 py-3 font-medium text-gray-500 text-xs uppercase tracking-wide">Description</th>
            <th className="px-4 py-3 font-medium text-gray-500 text-xs uppercase tracking-wide">Category</th>
            <th className="px-4 py-3 font-medium text-gray-500 text-xs uppercase tracking-wide text-right">Amount</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 bg-white">
          {transactions.map((tx) => {
            const amt = Number(tx.amount);
            return (
              <tr key={tx.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 text-gray-400 whitespace-nowrap tabular-nums">{tx.date}</td>
                <td className="px-4 py-3 text-gray-800 max-w-xs truncate">{tx.description}</td>
                <td className="px-4 py-3">
                  {tx.category && (
                    <span
                      className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                        CATEGORY_COLORS[tx.category] ?? "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {tx.category}
                    </span>
                  )}
                </td>
                <td
                  className={`px-4 py-3 font-medium text-right tabular-nums ${
                    amt >= 0 ? "text-emerald-600" : "text-gray-900"
                  }`}
                >
                  {amt >= 0 ? "+" : ""}${Math.abs(amt).toFixed(2)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
