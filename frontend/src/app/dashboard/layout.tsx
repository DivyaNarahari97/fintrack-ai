"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { UserButton } from "@clerk/nextjs";

const NAV = [
  { href: "/dashboard", label: "Overview" },
  { href: "/dashboard/upload", label: "Upload" },
  { href: "/dashboard/transactions", label: "Transactions" },
  { href: "/dashboard/chat", label: "Chat" },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex h-screen bg-gray-50">
      <aside className="w-56 bg-white border-r border-gray-200 flex flex-col shrink-0">
        <div className="p-5 border-b border-gray-200">
          <span className="text-base font-bold text-indigo-600">Finance Agent</span>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {NAV.map(({ href, label }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center px-3 py-2 text-sm rounded-lg transition-colors ${
                  active
                    ? "bg-indigo-50 text-indigo-700 font-medium"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                }`}
              >
                {label}
              </Link>
            );
          })}
        </nav>
        <div className="p-4 border-t border-gray-200">
          <UserButton afterSignOutUrl="/sign-in" />
        </div>
      </aside>
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
