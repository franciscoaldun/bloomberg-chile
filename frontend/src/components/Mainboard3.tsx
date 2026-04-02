"use client";

import CobrePanel from "./CobrePanel";
import CobreChart from "./CobreChart";
import FxMonitor from "./FxMonitor";
import LatamFxChart from "./LatamFxChart";

export default function Mainboard3() {
  return (
    <div className="flex-1 grid grid-cols-12 grid-rows-6 gap-0 min-h-0">
      {/* Cobre panel — left top */}
      <div className="col-span-3 row-span-3">
        <CobrePanel />
      </div>

      {/* Cobre chart — right top */}
      <div className="col-span-9 row-span-3">
        <CobreChart />
      </div>

      {/* FX Monitor — left bottom */}
      <div className="col-span-3 row-span-3">
        <FxMonitor />
      </div>

      {/* Latam FX comparison — right bottom */}
      <div className="col-span-9 row-span-3">
        <LatamFxChart />
      </div>
    </div>
  );
}
