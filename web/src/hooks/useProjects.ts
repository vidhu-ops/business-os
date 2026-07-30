"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, Project } from "@/lib/api";

const DEMO_WORKSPACE_ID = "demo_readonly";

function pickProjectId(
  projects: Project[],
  fromUrl: string | null,
  isDemo: boolean,
): string {
  const ids = new Set(projects.map((p) => p.workspace_id));
  if (fromUrl && ids.has(fromUrl)) {
    return fromUrl;
  }
  if (isDemo && ids.has(DEMO_WORKSPACE_ID)) {
    return DEMO_WORKSPACE_ID;
  }
  if (fromUrl === DEMO_WORKSPACE_ID && !isDemo) {
    // Ignore demo sample URL for real accounts.
    return projects[0]?.workspace_id || "";
  }
  return projects[0]?.workspace_id || "";
}

export function useProjects() {
  const searchParams = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [isDemo, setIsDemo] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    api
      .projects()
      .then((data) => {
        if (cancelled) return;
        const demo = Boolean(data.is_demo);
        setIsDemo(demo);
        setProjects(data.projects);
        const pick = pickProjectId(data.projects, searchParams.get("project"), demo);
        if (pick) setSelectedId(pick);
      })
      .catch((err) => {
        if (!cancelled) {
          setProjects([]);
          setError(err instanceof Error ? err.message : "Could not load projects");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [searchParams]);

  return { projects, selectedId, setSelectedId, loading, isDemo, error };
}
