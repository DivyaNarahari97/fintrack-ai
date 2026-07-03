"use client";
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { useAuth } from "@clerk/nextjs";
import { uploadStatement } from "@/lib/api";

interface Props {
  onUploaded?: () => void;
}

export default function UploadDropzone({ onUploaded }: Props) {
  const { getToken } = useAuth();
  const [status, setStatus] = useState<"idle" | "uploading" | "done" | "error">("idle");
  const [message, setMessage] = useState("");

  const onDrop = useCallback(
    async (accepted: File[]) => {
      const file = accepted[0];
      if (!file) return;
      setStatus("uploading");
      setMessage("");
      try {
        const token = await getToken();
        if (!token) throw new Error("Not authenticated");
        await uploadStatement(token, file);
        setStatus("done");
        setMessage("Uploaded successfully! Processing in the background…");
        onUploaded?.();
      } catch (err) {
        setStatus("error");
        setMessage(err instanceof Error ? err.message : "Upload failed");
      }
    },
    [getToken, onUploaded]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "text/csv": [".csv"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "application/vnd.ms-excel": [".xls"],
    },
    maxFiles: 1,
    disabled: status === "uploading",
  });

  return (
    <div>
      <div
        {...getRootProps()}
        className={[
          "border-2 border-dashed rounded-2xl p-14 text-center cursor-pointer transition-colors select-none",
          isDragActive ? "border-indigo-400 bg-indigo-50" : "border-gray-300 hover:border-indigo-300 hover:bg-gray-50",
          status === "uploading" ? "opacity-60 pointer-events-none" : "",
        ].join(" ")}
      >
        <input {...getInputProps()} />
        <div className="text-5xl mb-3 select-none">📄</div>
        {isDragActive ? (
          <p className="text-indigo-600 font-medium">Drop it here</p>
        ) : (
          <>
            <p className="text-gray-700 font-medium">Drag & drop your bank statement</p>
            <p className="text-sm text-gray-400 mt-1">or click to browse — PDF, CSV, XLSX · max 20 MB</p>
          </>
        )}
        {status === "uploading" && (
          <p className="text-sm text-indigo-500 mt-3 animate-pulse">Uploading…</p>
        )}
      </div>
      {message && (
        <p className={`mt-3 text-sm ${status === "error" ? "text-red-600" : "text-emerald-600"}`}>
          {message}
        </p>
      )}
    </div>
  );
}
