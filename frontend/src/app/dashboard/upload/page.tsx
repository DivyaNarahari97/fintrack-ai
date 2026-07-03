"use client";
import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { fetchStatements, deleteStatement, type Statement } from "@/lib/api";
import UploadDropzone from "@/components/upload-dropzone";

export default function UploadPage() {
  const { getToken } = useAuth();
  const [statements, setStatements] = useState<Statement[]>([]);

  const refresh = async () => {
    const token = await getToken();
    if (!token) return;
    setStatements(await fetchStatements(token));
  };

  useEffect(() => { refresh(); }, []);

  const handleDelete = async (id: string) => {
    const token = await getToken();
    if (!token) return;
    await deleteStatement(token, id);
    await refresh();
  };

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <h2 className="text-2xl font-bold mb-2">Upload Statement</h2>
      <p className="text-sm text-gray-500 mb-6">
        Supported formats: PDF, CSV, XLSX. Transactions are categorized automatically by AI.
      </p>
      <UploadDropzone onUploaded={refresh} />

      {statements.length > 0 && (
        <div className="mt-10">
          <h3 className="text-base font-semibold mb-3">Uploaded Statements</h3>
          <div className="space-y-2">
            {statements.map((s) => (
              <div
                key={s.id}
                className="bg-white border border-gray-200 rounded-xl px-4 py-3 flex justify-between items-center"
              >
                <div>
                  <p className="text-sm font-medium text-gray-800">{s.filename}</p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {new Date(s.uploaded_at).toLocaleString()}
                    {s.error_message && (
                      <span className="text-red-500 ml-2">{s.error_message}</span>
                    )}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <StatusBadge status={s.status} />
                  <button
                    onClick={() => handleDelete(s.id)}
                    className="text-xs text-gray-400 hover:text-red-500 transition-colors"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const palette: Record<string, string> = {
    processing: "bg-amber-100 text-amber-700",
    done: "bg-emerald-100 text-emerald-700",
    error: "bg-red-100 text-red-700",
  };
  return (
    <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${palette[status] ?? "bg-gray-100 text-gray-600"}`}>
      {status}
    </span>
  );
}
