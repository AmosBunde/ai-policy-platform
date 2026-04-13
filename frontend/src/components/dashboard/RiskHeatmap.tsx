import { useNavigate } from "react-router-dom";
import { clsx } from "clsx";
import { Card } from "../ui/Card";

interface HeatmapCell {
  region: string;
  category: string;
  score: number;
}

interface RiskHeatmapProps {
  data: HeatmapCell[];
  loading?: boolean;
}

const REGIONS = ["EU", "US-Federal", "UK", "APAC", "Canada", "LatAm"];
const CATEGORIES = ["privacy", "safety", "IP", "antitrust", "transparency", "liability"];

function getColor(score: number): string {
  if (score >= 8) return "bg-danger/80 text-white";
  if (score >= 6) return "bg-orange-400/70 text-white";
  if (score >= 4) return "bg-accent/60 text-navy-900";
  if (score >= 2) return "bg-amber-200/60 text-navy-900";
  if (score > 0) return "bg-success/30 text-navy-900";
  return "bg-slate-100 dark:bg-slate-800 text-slate-400";
}

function HeatmapSkeleton() {
  return (
    <Card>
      <div className="animate-pulse">
        <div className="h-5 w-32 bg-slate-200 dark:bg-slate-700 rounded mb-4" />
        <div className="h-48 bg-slate-100 dark:bg-slate-800 rounded" />
      </div>
    </Card>
  );
}

export function RiskHeatmap({ data, loading }: RiskHeatmapProps) {
  const navigate = useNavigate();

  if (loading) return <HeatmapSkeleton />;

  const scoreMap = new Map<string, number>();
  for (const cell of data) {
    scoreMap.set(`${cell.region}:${cell.category}`, cell.score);
  }

  const handleCellClick = (region: string, category: string) => {
    navigate(`/documents?jurisdiction=${encodeURIComponent(region)}&category=${encodeURIComponent(category)}`);
  };

  return (
    <Card>
      <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-4">
        Risk Heatmap
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr>
              <th className="text-left p-1 text-slate-500" />
              {CATEGORIES.map((cat) => (
                <th key={cat} className="p-1 text-slate-500 font-medium capitalize text-center">
                  {cat}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {REGIONS.map((region) => (
              <tr key={region}>
                <td className="p-1 text-slate-600 dark:text-slate-400 font-medium whitespace-nowrap">
                  {region}
                </td>
                {CATEGORIES.map((cat) => {
                  const score = scoreMap.get(`${region}:${cat}`) ?? 0;
                  return (
                    <td key={cat} className="p-1">
                      <button
                        onClick={() => handleCellClick(region, cat)}
                        className={clsx(
                          "w-full h-8 rounded text-[10px] font-bold transition-transform hover:scale-105 cursor-pointer",
                          getColor(score),
                        )}
                        title={`${region} / ${cat}: ${score}/10`}
                      >
                        {score > 0 ? score : ""}
                      </button>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
