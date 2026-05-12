"use client";

import { useEffect, useRef, useState } from "react";
import type { TradePlan } from "@/lib/types";

interface Props {
  symbol: string;
  kind: "stock_us" | "stock_kr" | "coin";
  plan?: TradePlan | null;
  height?: number;
}

type Bar = {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

export function TradePlanChart({ symbol, kind, plan, height = 360 }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (!containerRef.current) return;
    let chart: import("lightweight-charts").IChartApi | null = null;
    let resizeObs: ResizeObserver | null = null;
    let cancelled = false;

    (async () => {
      try {
        const [{ createChart, CandlestickSeries, LineSeries, AreaSeries, CrosshairMode }] = await Promise.all([
          import("lightweight-charts"),
        ]);
        if (cancelled || !containerRef.current) return;

        chart = createChart(containerRef.current, {
          height,
          layout: {
            background: { color: "transparent" },
            textColor: "#cbd5e1",
            fontFamily: "ui-sans-serif, system-ui, sans-serif",
          },
          grid: {
            vertLines: { color: "rgba(148, 163, 184, 0.1)" },
            horzLines: { color: "rgba(148, 163, 184, 0.1)" },
          },
          rightPriceScale: { borderVisible: false },
          timeScale: { borderVisible: false, secondsVisible: false },
          crosshair: { mode: CrosshairMode.Normal },
        });

        const r = await fetch(
          `/api/history?kind=${kind}&symbol=${encodeURIComponent(symbol)}`,
          { cache: "default" },
        );
        if (!r.ok) throw new Error(`history ${r.status}`);
        const { bars } = (await r.json()) as { bars: Bar[] };
        if (cancelled || !bars?.length) {
          setError("가격 history 없음");
          return;
        }

        const candles = chart.addSeries(CandlestickSeries, {
          upColor: "#10b981",
          downColor: "#f43f5e",
          borderVisible: false,
          wickUpColor: "#10b981",
          wickDownColor: "#f43f5e",
        });
        candles.setData(
          bars.map((b) => ({
            time: b.time as import("lightweight-charts").UTCTimestamp,
            open: b.open,
            high: b.high,
            low: b.low,
            close: b.close,
          })),
        );

        // Plan overlay — entry, stop, targets
        if (plan && plan.actionable) {
          const first = bars[0].time as import("lightweight-charts").UTCTimestamp;
          const last = bars[bars.length - 1].time as import("lightweight-charts").UTCTimestamp;

          const addLevelLine = (price: number, color: string, label: string) => {
            const s = chart!.addSeries(LineSeries, {
              color,
              lineWidth: 2,
              lineStyle: 2,
              priceLineVisible: false,
              lastValueVisible: false,
              crosshairMarkerVisible: false,
            });
            s.setData([
              { time: first, value: price },
              { time: last, value: price },
            ]);
            // Static label via priceLine
            s.createPriceLine({
              price,
              color,
              lineWidth: 1,
              lineStyle: 2,
              axisLabelVisible: true,
              title: label,
            });
          };

          // Entry zone — green band as area between entry_low and entry_high
          if (plan.entry_low && plan.entry_high && plan.entry_high > plan.entry_low) {
            const band = chart.addSeries(AreaSeries, {
              topColor: "rgba(16, 185, 129, 0.2)",
              bottomColor: "rgba(16, 185, 129, 0.05)",
              lineColor: "rgba(16, 185, 129, 0.5)",
              lineWidth: 1,
              priceLineVisible: false,
              lastValueVisible: false,
            });
            band.setData([
              { time: first, value: plan.entry_high },
              { time: last, value: plan.entry_high },
            ]);
          }

          addLevelLine(plan.entry, "#10b981", "Entry");
          addLevelLine(plan.stop_loss, "#f43f5e", "SL");
          plan.targets.forEach((t, i) => {
            addLevelLine(t.price, "#38bdf8", `T${i + 1}`);
          });

          // Other confluence zones (faded)
          plan.zones
            .filter((z) => z.weight >= 1.5)
            .slice(0, 6)
            .forEach((z) => {
              const s = chart!.addSeries(LineSeries, {
                color: "rgba(148, 163, 184, 0.35)",
                lineWidth: 1,
                lineStyle: 3,
                priceLineVisible: false,
                lastValueVisible: false,
                crosshairMarkerVisible: false,
              });
              s.setData([
                { time: first, value: z.center },
                { time: last, value: z.center },
              ]);
            });
        }

        chart.timeScale().fitContent();
        setLoaded(true);

        // Responsive
        resizeObs = new ResizeObserver(() => {
          if (chart && containerRef.current) {
            chart.applyOptions({ width: containerRef.current.clientWidth });
          }
        });
        resizeObs.observe(containerRef.current);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "chart failed");
      }
    })();

    return () => {
      cancelled = true;
      resizeObs?.disconnect();
      chart?.remove();
    };
  }, [symbol, kind, plan, height]);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-3">
      <div className="flex items-center justify-between mb-2 text-xs">
        <div className="text-slate-300 font-medium">
          📈 일봉 (180일) — 컨플루언스 zone overlay
        </div>
        <div className="text-slate-500">
          {plan?.actionable ? (
            <>
              <span className="text-emerald-400">━</span> Entry{" "}
              <span className="text-rose-400">━</span> SL{" "}
              <span className="text-sky-400">━</span> Target
            </>
          ) : (
            "Plan inactive"
          )}
        </div>
      </div>
      <div ref={containerRef} style={{ height }} />
      {error && (
        <div className="mt-2 text-xs text-slate-500">차트 로드 실패: {error}</div>
      )}
      {!loaded && !error && (
        <div className="mt-2 text-xs text-slate-500">차트 로딩 중…</div>
      )}
    </div>
  );
}
