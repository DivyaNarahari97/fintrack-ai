"use client";
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from "recharts";
import type { CategoryTotal, MonthlyTotal } from "@/lib/api";

const COLORS = [
  "#6366f1", "#8b5cf6", "#ec4899", "#f59e0b",
  "#10b981", "#3b82f6", "#ef4444", "#14b8a6",
];

type Props =
  | { type: "pie"; data: CategoryTotal[] }
  | { type: "bar"; data: MonthlyTotal[] };

export default function SpendingChart(props: Props) {
  if (props.type === "pie") {
    const data = props.data.map((d) => ({ name: d.category, value: Number(d.total) }));
    return (
      <ResponsiveContainer width="100%" height={220}>
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={75}>
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(v: number) => `$${v.toFixed(2)}`} />
          <Legend iconSize={10} iconType="circle" />
        </PieChart>
      </ResponsiveContainer>
    );
  }

  const data = props.data.map((d) => ({ month: d.month, total: Number(d.total) }));
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
        <XAxis dataKey="month" tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `$${v}`} width={56} />
        <Tooltip formatter={(v: number) => `$${v.toFixed(2)}`} />
        <Bar dataKey="total" fill="#6366f1" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
