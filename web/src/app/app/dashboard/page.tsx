"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api, Project } from "@/lib/api";
export default function DashboardPage(){const [projects,setProjects]=useState<Project[]>([]);useEffect(()=>{api.projects().then(d=>setProjects(d.projects)).catch(()=>setProjects([]));},[]);return(<div className="space-y-8"><div><h1 className="font-display text-3xl font-bold">Welcome back</h1></div><Link href="/app/workspace" className="iid-btn iid-btn-primary">Open workspace</Link></div>);}
