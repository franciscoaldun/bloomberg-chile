"use client";

import CorrelationHeatmap from "./CorrelationHeatmap";
import InvestmentSimulator from "./InvestmentSimulator";
import AnalysisPanel from "./AnalysisPanel";
import EconomicCalendar from "./EconomicCalendar";

export default function Mainboard2() {
  return (
    <div className="flex-1 grid grid-cols-12 grid-rows-6 gap-0 min-h-0">
      {/* Briefing IA — left column top */}
      <div className="col-span-3 row-span-3">
        <AnalysisPanel />
      </div>

      {/* Investment Simulator — top center+right */}
      <div className="col-span-9 row-span-4">
        <InvestmentSimulator />
      </div>

      {/* Economic Calendar — left column bottom */}
      <div className="col-span-3 row-span-3">
        <EconomicCalendar />
      </div>

      {/* Correlation Heatmap — bottom center+right */}
      <div className="col-span-9 row-span-2">
        <CorrelationHeatmap />
      </div>
    </div>
  );
}
