import "./globals.css";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
export const metadata={title:"BrewSpare",description:"AI spare parts demand and predictive maintenance planner"};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body><div className="shell"><Sidebar/><main className="main"><Header/>{children}</main></div></body></html>}
