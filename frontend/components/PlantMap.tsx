"use client";
import { colorFor } from "./StatusBadge";

type Asset={asset_code:string;name:string;area:string;status:string;risk_score:number;health_score:number;x:number;y:number};
export default function PlantMap({assets,selected,onSelect}:{assets:Asset[],selected?:string,onSelect:(a:Asset)=>void}){
  const ordered=assets.filter(a=>a.asset_code!=="AC-01");
  return <div className="plantmap"><div className="process-title">Brewery Process Connectivity<span className="process-sub">Click equipment to inspect machine → spare-part risk</span></div>
    {ordered.map((a,i)=>{const left=7+i*(86/(Math.max(1,ordered.length-1)));return <div key={`pipe-${a.asset_code}`} className="pipe" style={{left:`${left}%`,width:i===ordered.length-1?0:`${86/(Math.max(1,ordered.length-1))}%`}}/>})}
    {ordered.map((a,i)=>{const left=7+i*(86/(Math.max(1,ordered.length-1)));return <button aria-label={a.name} onClick={()=>onSelect(a)} key={a.asset_code} className={`asset-node ${selected===a.asset_code?"selected":""}`} style={{left:`${left}%`,top:"53%",background:"transparent",border:0}}><div className={`machine ${a.asset_code==="PKG-01"?"robot":""}`}><span className="status-ring" style={{background:colorFor(a.status)}}/></div><div className="node-label">{a.name.replace(/ 04| 01| 02/g,"")}</div><div className="node-code">{a.asset_code}</div></button>})}
    {assets.filter(a=>a.asset_code==="AC-01").map(a=><button key={a.asset_code} onClick={()=>onSelect(a)} className={`asset-node ${selected===a.asset_code?"selected":""}`} style={{left:"54%",top:"82%",background:"transparent",border:0}}><div className="machine"><span className="status-ring" style={{background:colorFor(a.status)}}/></div><div className="node-label">Air Compressor</div><div className="node-code">AC-01</div></button>)}
  </div>
}
