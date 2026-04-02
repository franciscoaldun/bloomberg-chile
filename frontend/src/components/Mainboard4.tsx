"use client";

import YieldCurveSnapshot from "./YieldCurveSnapshot";
import YieldCurveChart from "./YieldCurveChart";
import TpmTimeline from "./TpmTimeline";
import EofChart from "./EofChart";

export default function Mainboard4() {
  return (
    <div className="flex-1 grid grid-cols-12 grid-rows-6 gap-0 min-h-0">
      {/* Yield curve snapshot — left top */}
      <div className="col-span-3 row-span-3">
        <YieldCurveSnapshot />
      </div>

      {/* Yield curve chart — right top */}
      <div className="col-span-9 row-span-3">
        <YieldCurveChart />
      </div>

      {/* TPM decisions timeline — left bottom */}
      <div className="col-span-5 row-span-3">
        <TpmTimeline />
      </div>

      {/* EOF expectations chart — right bottom */}
      <div className="col-span-7 row-span-3">
        <EofChart />
      </div>
    </div>
  );
}
