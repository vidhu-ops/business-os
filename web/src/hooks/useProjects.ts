"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, Project } from "@/lib/api";

export function useProjects() {
  const searchParams = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .projects()
      .then((data) => {
        setProjects(data.projects);
        const fromUrl = searchParams.get("project");
        const pick = fromUrl || data.projects[0]?.workspace_id || "";
        if (pick) setSelectedId(pick);
      })
      .catch(() => setProjects([]))
      .finally(() => setLoading(false));
  }, [searchParams]);

  return { projects, selectedId, setSelectedId, loading };
}