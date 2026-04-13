import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Card } from "../ui/Card";

interface ActivityDataPoint {
  date: string;
  documents: number;
  enriched: number;
}

interface ActivityChartProps {
  data: ActivityDataPoint[];
  loading?: boolean;
}

function ChartSkeleton() {
  return (
    <Card>
      <div className="animate-pulse">
        <div className="h-5 w-40 bg-slate-200 dark:bg-slate-700 rounded mb-4" />
        <div className="h-64 bg-slate-100 dark:bg-slate-800 rounded" />
      </div>
    </Card>
  );
}

export function ActivityChart({ data, loading }: ActivityChartProps) {
  if (loading) return <ChartSkeleton />;

  return (
    <Card>
      <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-4">
        Regulatory Activity (30 days)
      </h3>
      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <defs>
            <linearGradient id="docGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#F59E0B" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="enrichGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10B981" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
          <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#94A3B8" }} />
          <YAxis tick={{ fontSize: 11, fill: "#94A3B8" }} />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1E293B",
              border: "1px solid #334155",
              borderRadius: "8px",
              fontSize: "12px",
            }}
            labelStyle={{ color: "#94A3B8" }}
          />
          <Area
            type="monotone"
            dataKey="documents"
            stroke="#F59E0B"
            fill="url(#docGradient)"
            strokeWidth={2}
            name="Ingested"
          />
          <Area
            type="monotone"
            dataKey="enriched"
            stroke="#10B981"
            fill="url(#enrichGradient)"
            strokeWidth={2}
            name="Enriched"
          />
        </AreaChart>
      </ResponsiveContainer>
    </Card>
  );
}
