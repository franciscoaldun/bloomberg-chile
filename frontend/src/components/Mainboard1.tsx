"use client";

import MacroPanel from "@/components/MacroPanel";
import QuoteDisplay from "@/components/QuoteDisplay";
import PriceChart from "@/components/PriceChart";
import { Indicator } from "@/types/series";
import { SeriesResponse } from "@/types/series";

interface Mainboard1Props {
  indicators: Indicator[];
  selectedId: string;
  selectedSeries: SeriesResponse | null;
  onSelect: (id: string) => void;
}

export default function Mainboard1({
  indicators,
  selectedId,
  selectedSeries,
  onSelect,
}: Mainboard1Props) {
  const dailyIndicators = indicators.filter((i) =>
    ["tpm", "usd_clp", "ipsa", "uf"].includes(i.id)
  );
  const monthlyIndicators = indicators.filter((i) =>
    ["imacec", "desempleo", "ipc_var", "base_monetaria", "reservas_intl", "export_mineras"].includes(i.id)
  );
  const quarterlyIndicators = indicators.filter((i) =>
    ["deuda_pib", "cuenta_corriente"].includes(i.id)
  );

  const selectedIndicator = indicators.find((i) => i.id === selectedId);

  const chartColor = selectedIndicator?.change_pct
    ? selectedIndicator.change_pct >= 0
      ? "#3BBA13"
      : "#FF433D"
    : "#FF9900";

  return (
    <div className="flex-1 grid grid-cols-12 grid-rows-6 gap-0 min-h-0">
      {/* Quote Display — top left */}
      <div className="col-span-3 row-span-2">
        {selectedIndicator && <QuoteDisplay indicator={selectedIndicator} />}
      </div>

      {/* Main Chart — top center+right */}
      <div className="col-span-9 row-span-4">
        {selectedSeries && (
          <PriceChart
            seriesId={selectedId}
            data={selectedSeries.data}
            title={selectedSeries.name}
            unit={selectedSeries.unit}
            color={chartColor}
          />
        )}
      </div>

      {/* Daily indicators panel — left middle */}
      <div className="col-span-3 row-span-4">
        <MacroPanel
          title="MERCADO DIARIO"
          indicators={dailyIndicators}
          onSelect={onSelect}
          selectedId={selectedId}
        />
      </div>

      {/* Monthly indicators — bottom center */}
      <div className="col-span-5 row-span-2">
        <MacroPanel
          title="INDICADORES MENSUALES"
          indicators={monthlyIndicators}
          onSelect={onSelect}
          selectedId={selectedId}
        />
      </div>

      {/* Quarterly indicators — bottom right */}
      <div className="col-span-4 row-span-2">
        <MacroPanel
          title="INDICADORES TRIMESTRALES / FISCAL"
          indicators={quarterlyIndicators}
          onSelect={onSelect}
          selectedId={selectedId}
        />
      </div>
    </div>
  );
}
