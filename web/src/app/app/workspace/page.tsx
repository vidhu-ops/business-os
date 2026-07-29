import { redirect } from "next/navigation";

export default function WorkspaceRedirectPage({
  searchParams,
}: {
  searchParams: { project?: string };
}) {
  const q = searchParams.project ? `?project=${encodeURIComponent(searchParams.project)}` : "";
  redirect(`/app/research${q}`);
}