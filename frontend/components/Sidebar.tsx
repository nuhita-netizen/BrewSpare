"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const items = [
  ["/","⌂","Plant Overview"],["/assets","◫","Assets"],["/spare-parts","⚙","Spare Parts"],["/maintenance","⌁","Maintenance"],["/inventory","▣","Inventory"],["/procurement","◇","Procurement"],["/ai-insights","✦","AI Insights"],["/reports","▤","Reports"],["/scenario-simulator","⌘","Scenario Simulator"],["/settings","⚙","Settings"]
];
export default function Sidebar(){
  const path=usePathname();
  return <aside className="sidebar">
    <div className="brand"><div className="brand-mark">B</div><div><h1>BrewSpare</h1><small>AI Maintenance Intelligence</small></div></div>
    <nav className="nav">{items.map(([href,ico,label])=><Link key={href} className={path===href|| (href!=="/"&&path.startsWith(href))?"active":""} href={href}><span className="nav-ico">{ico}</span><span>{label}</span></Link>)}</nav>
    <div className="plant-chip"><b>RiverStone Brewery</b><br/><span style={{color:"var(--muted)"}}>Plant 01</span></div>
  </aside>
}
