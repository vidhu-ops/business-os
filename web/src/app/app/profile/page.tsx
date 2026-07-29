"use client";
import { api } from "@/lib/api";
import { useRouter } from "next/navigation";
export default function ProfilePage(){const r=useRouter();return(<div><h1 className="font-display text-3xl font-bold">Profile</h1><button className="iid-btn iid-btn-ghost" onClick={async()=>{await api.logout();r.push("/login");}}>Log out</button></div>);}
