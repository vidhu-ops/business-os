"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function SavedFilesPage() {
  const [files, setFiles] = useState<Array<Record<string, string | number>>>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api.files()
      .then((data) => setFiles(data.files))
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load files"));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl font-bold">Saved files</h1>
        <p className="mt-2 muted">Exports and deliverables from your workspace runs.</p>
      </div>
      <section className="iid-card overflow-x-auto">
        {error && <p className="text-sm text-red-400">{error}</p>}
        {files.length === 0 && !error ? (
          <p className="muted">No saved files yet.</p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="muted">
              <tr>
                <th className="pb-2">Name</th>
                <th className="pb-2">Folder</th>
                <th className="pb-2">Type</th>
                <th className="pb-2">Modified</th>
              </tr>
            </thead>
            <tbody>
              {files.map((file) => (
                <tr key={String(file.path)} className="border-t border-[var(--iid-line)]">
                  <td className="py-2 pr-4">{file.name}</td>
                  <td className="py-2 pr-4">{file.folder}</td>
                  <td className="py-2 pr-4">{file.type}</td>
                  <td className="py-2">{file.modified}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
