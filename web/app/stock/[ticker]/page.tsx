import { notFound } from "next/navigation";
import { loadLatest } from "@/lib/data";
import { DetailView } from "@/components/detail-view";

export const revalidate = 3600;

export async function generateStaticParams() {
  const ctx = await loadLatest("stock");
  return ctx.verdicts.map((v) => ({ ticker: v.ticker }));
}

export default async function StockDetail({
  params,
}: {
  params: Promise<{ ticker: string }>;
}) {
  const { ticker } = await params;
  const ctx = await loadLatest("stock");
  const verdict = ctx.verdicts.find(
    (v) => v.ticker.toLowerCase() === ticker.toLowerCase(),
  );
  if (!verdict) notFound();
  return <DetailView verdict={verdict} asset="stock" />;
}
