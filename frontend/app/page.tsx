"use client";
import { useEffect,useMemo,useState } from "react";
import PlantMap from "@/components/PlantMap";
import StatusBadge,{colorFor} from "@/components/StatusBadge";
import Sparkline from "@/components/Sparkline";
import { api } from "@/lib/api";

type Asset={asset_code:string;name:string;area:string;status:string;risk_score:number;health_score:number;x:number;y:number};
type Part={part_code:string;part_name:string;usable_stock:number;forecast:{d30:number};lead_time_days:number;state:string;recommended_order_qty:number;availability_gap_days:number};
type Summary={plant:{name:string};counts:Record<string,number>;plant_availability:number;potential_downtime_exposure:number;avoidable_inventory_value:number;assets:Asset[];critical_assets:Asset[];parts_to_order:Part[]};
type Detail={asset_code:string;name:string;health_score:number;risk_score:number;status:string;next_maintenance_days:number;latest_sensor?:{temperature:number;vibration:number;pressure:number;output_rate:number};parts:Part[]};

const money=(n:number)=>`₹${(n/100000).toFixed(1)}L`;
export default function Home(){
 const [data,setData]=useState<Summary|null>(null),[selected,setSelected]=useState("FL-01"),[detail,setDetail]=useState<Detail|null>(null),[err,setErr]=useState("");
 useEffect(()=>{api<Summary>("/plant-summary").then(setData).catch(e=>setErr(e.message))},[]);
 useEffect(()=>{api<Detail>(`/assets/${selected}`).then(setDetail).catch(()=>{})},[selected]);
 const sensors=detail?.latest_sensor;
 const mockSeries=useMemo(()=>Array.from({length:14},(_,i)=>4.4+i*.25+Math.sin(i)*.35),[]);
 if(err)return <div className="content"><div className="notice red">Backend unavailable: {err}. Start FastAPI on port 8000.</div></div>;
 if(!data)return <div className="content"><div className="section">Loading BrewSpare command center…</div></div>;
 return <div className="content">
   <div className="tabs"><span className="tab active">Overview</span><span className="tab">Live Data</span><span className="tab">Diagnostics</span><span className="tab">Process Flow</span><span className="tab">Spare Parts</span><span className="tab">Maintenance</span><div className="controls"><select className="select"><option>Brew Line 1</option></select><select className="select"><option>Real-time</option><option>24 hours</option></select></div></div>
   <section className="metrics">
    <div className="metric"><div className="value"><i className="dot" style={{background:"var(--green)"}}/>{data.counts.GREEN}</div><div className="label">Healthy Assets</div></div>
    <div className="metric"><div className="value"><i className="dot" style={{background:"var(--yellow)"}}/>{data.counts.YELLOW}</div><div className="label">Monitor</div></div>
    <div className="metric"><div className="value"><i className="dot" style={{background:"var(--orange)"}}/>{data.counts.ORANGE}</div><div className="label">High Risk</div></div>
    <div className="metric"><div className="value"><i className="dot" style={{background:"var(--red)"}}/>{data.counts.RED}</div><div className="label">Critical</div></div>
    <div className="metric"><div className="value">{data.plant_availability}%</div><div className="label">Plant Availability</div></div>
    <div className="metric"><div className="value">{money(data.potential_downtime_exposure)}</div><div className="label">Potential Downtime Exposure</div></div>
    <div className="metric"><div className="value">{money(data.avoidable_inventory_value)}</div><div className="label">Avoidable Inventory Value</div></div>
   </section>
   <section className="hero">
    <PlantMap assets={data.assets} selected={selected} onSelect={a=>setSelected(a.asset_code)}/>
    <aside className="sidepanel">
      <div className="panel-head"><div><span className="subtle">Selected asset</span><h3>{detail?.asset_code} · {detail?.name}</h3></div><span className={`tag ${(detail?.status||"green").toLowerCase()}`}>{detail?.status||"Loading"}</span></div>
      <div><div className="kv"><span>Health Score</span><b>{detail?.health_score ?? "—"}%</b></div><div className="kv"><span>Predictive Risk</span><b style={{color:colorFor(detail?.status||"")}}>{detail?.risk_score ?? "—"}%</b></div><div className="kv"><span>Next Maintenance</span><b>{detail?.next_maintenance_days ?? "—"} days</b></div></div>
      <div><div className="subtle">Risk level</div><div className="riskbar" style={{marginTop:7}}><i style={{width:`${detail?.risk_score||0}%`,background:colorFor(detail?.status||"")}}/></div></div>
      <div><div className="subtle">Required / dependent parts</div>{detail?.parts?.slice(0,3).map(p=><div className="part-row" key={p.part_code}><i className="row-dot" style={{background:colorFor(p.state)}}/><div><div className="row-title">{p.part_code}</div><div className="row-meta">{p.part_name}</div></div><b>{p.usable_stock} / {p.forecast.d30}</b></div>)}</div>
      <div className="panel-actions"><a href={`/assets/${selected}`} className="btn">View Details</a><a href="/maintenance" className="btn secondary">Plan Maintenance</a></div>
    </aside>
   </section>
   <section className="grid">
    <div className="card"><h3>Live Sensor Data <span className="subtle">· {detail?.asset_code}</span></h3><div className="sensor-grid">
      <div className="sensor"><span className="subtle">Temperature</span><b>{sensors?.temperature ?? 67.2} °C</b><Sparkline values={mockSeries.map((x,i)=>60+x+i*.08)} color="#f27a3d"/></div>
      <div className="sensor"><span className="subtle">Vibration</span><b>{sensors?.vibration ?? 8.1} mm/s</b><Sparkline values={mockSeries} color="#ef4d55"/></div>
      <div className="sensor"><span className="subtle">Pressure</span><b>{sensors?.pressure ?? 5.6} bar</b><Sparkline values={mockSeries.map(x=>x*.55)} color="#246bfd"/></div>
      <div className="sensor"><span className="subtle">Output Rate</span><b>{Math.round(sensors?.output_rate ?? 17420).toLocaleString()}</b><Sparkline values={[15,17,16,18,17,18,19,17,18,17,18,17,16,17]} color="#2fbd83"/></div>
    </div></div>
    <div className="card"><h3>Production Flow</h3><div style={{display:"flex",alignItems:"center",gap:7,flexWrap:"wrap",marginTop:28}}>{["Mixing","Boiling","Fermentation","Filtration","Filling","Packaging"].map(x=><span key={x} className="tag" style={{background:x==="Filling"?"#ffecee":"#edf4ff",color:x==="Filling"?"#c52f39":"#3f5f92"}}>{x}</span>)}</div><div style={{marginTop:28}} className="notice">Connectivity shows where a machine issue can interrupt the downstream brewery process.</div></div>
    <div className="card"><h3>Critical Assets</h3>{data.critical_assets.map(a=><a className="asset-row" href={`/assets/${a.asset_code}`} key={a.asset_code}><i className="row-dot" style={{background:colorFor(a.status)}}/><div><div className="row-title">{a.asset_code} · {a.name}</div><div className="row-meta">Health {a.health_score}%</div></div><div className="row-risk" style={{color:colorFor(a.status)}}>{a.risk_score}%</div></a>)}</div>
    <div className="card"><h3>Parts to Order</h3>{data.parts_to_order.map(p=><a href={`/spare-parts/${p.part_code}`} className="part-row" key={p.part_code}><i className="row-dot" style={{background:colorFor(p.state)}}/><div><div className="row-title">{p.part_code}</div><div className="row-meta">{p.part_name} · Stock {p.usable_stock} · Need {p.forecast.d30}</div></div><div className="row-risk">Order {p.recommended_order_qty}</div></a>)}</div>
   </section>
   <div className="ai-bar"><span style={{color:"var(--blue)",fontSize:20}}>✦</span><input className="ai-input" placeholder="Ask BrewSpare AI… e.g. ‘What should we order this week?’"/><span className="chip">What needs attention today?</span><span className="chip">Which parts are at risk?</span><a className="btn" href="/ai-insights">Ask</a></div>
 </div>
}
