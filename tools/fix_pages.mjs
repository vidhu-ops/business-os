import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
const root = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "web", "src", "app", "app");
const o = "<" + "div";
const c = "</" + "motion.div>";
const pages = {
"dashboard/page.tsx": `"use client";\nimport Link from \"next/link\";\nimport { useEffect, useState } from \"react\";\nimport { api, Project } from \"@/lib/api\";\nexport default function DashboardPage(){const [projects,setProjects]=useState([]);useEffect(()=>{api.projects().then(d=>setProjects(d.projects)).catch(()=>setProjects([]));},[]);return(<DIV className=\"space-y-8\"><DIV><h1 className=\"font-display text-3xl font-bold\">Welcome back</h1></DIV><Link href=\"/app/workspace\" className=\"iid-btn iid-btn-primary\">Open workspace</Link></DIV>);}\n`,
"workspace/page.tsx": `"use client";\nexport default function WorkspacePage(){return(<DIV className=\"space-y-6\"><h1 className=\"font-display text-3xl font-bold\">Workspace</h1><p className=\"muted\">Research tools connect to the FastAPI backend.</p></DIV>);}\n`,
"saved/page.tsx": `"use client";\nexport default function SavedPage(){return(<DIV><h1 className=\"font-display text-3xl font-bold\">Saved files</h1></DIV>);}\n`,
"profile/page.tsx": `"use client";\nimport { api } from \"@/lib/api\";\nimport { useRouter } from \"next/navigation\";\nexport default function ProfilePage(){const r=useRouter();return(<DIV><h1 className=\"font-display text-3xl font-bold\">Profile</h1><button className=\"iid-btn iid-btn-ghost\" onClick={async()=>{await api.logout();r.push(\"/login\");}}>Log out</button></DIV>);}\n`,
};
for (const [rel, raw] of Object.entries(pages)) {
  const content = raw.replaceAll("<DIV", o).replaceAll("</DIV>", c).replaceAll("</motion.div>", "</div>");
  const file = path.join(root, rel);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, content, "utf8");
}