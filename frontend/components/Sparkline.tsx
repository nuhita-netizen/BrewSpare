export default function Sparkline({values,color="#246bfd"}:{values:number[],color?:string}){
  const w=120,h=34;if(values.length<2)return null;const min=Math.min(...values),max=Math.max(...values);const pts=values.map((v,i)=>`${i*(w/(values.length-1))},${h-4-(v-min)/Math.max(1,max-min)*(h-8)}`).join(" ");
  return <svg className="spark" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none"><polyline fill="none" stroke={color} strokeWidth="2" points={pts}/></svg>
}
