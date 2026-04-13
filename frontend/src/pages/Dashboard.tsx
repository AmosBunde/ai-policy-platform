import { useState } from "react";
import { FileText, AlertTriangle, ClipboardList, ShieldAlert } from "lucide-react";
import { KPICard } from "../components/dashboard/KPICard";
import { ActivityChart } from "../components/dashboard/ActivityChart";
import { RiskHeatmap } from "../components/dashboard/RiskHeatmap";
import { RecentDocuments } from "../components/dashboard/RecentDocuments";
import { RefreshControl } from "../components/dashboard/RefreshControl";
import {
  useDashboardKPIs,
  useDashboardActivity,
  useDashboardHeatmap,
  useRecentDocuments,
} from "../hooks/useDashboard";

export default function Dashboard() {
  const [refreshInterval, setRefreshInterval] = useState<number | null>(30_000);
  const interval = refreshInterval ?? false;

  const kpis = useDashboardKPIs(interval);
  const activity = useDashboardActivity(interval);
  const heatmap = useDashboardHeatmap(interval);
  const recent = useRecentDocuments(interval);

  const k = kpis.data;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <RefreshControl interval={refreshInterval} onIntervalChange={setRefreshInterval} />
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          label="Total Documents"
          value={k?.totalDocuments ?? 0}
          icon={<FileText className="h-5 w-5" />}
          trend={k?.documentsTrend}
          trendLabel={k?.documentsTrendLabel}
          loading={kpis.isLoading}
        />
        <KPICard
          label="Pending Reviews"
          value={k?.pendingReviews ?? 0}
          icon={<AlertTriangle className="h-5 w-5" />}
          trend={k?.pendingTrend}
          trendLabel={k?.pendingTrendLabel}
          loading={kpis.isLoading}
        />
        <KPICard
          label="High Urgency"
          value={k?.highUrgency ?? 0}
          icon={<ShieldAlert className="h-5 w-5" />}
          trend={k?.urgencyTrend}
          trendLabel={k?.urgencyTrendLabel}
          loading={kpis.isLoading}
        />
        <KPICard
          label="Reports Generated"
          value={k?.reportsGenerated ?? 0}
          icon={<ClipboardList className="h-5 w-5" />}
          trend={k?.reportsTrend}
          trendLabel={k?.reportsTrendLabel}
          loading={kpis.isLoading}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ActivityChart data={activity.data ?? []} loading={activity.isLoading} />
        <RiskHeatmap data={heatmap.data ?? []} loading={heatmap.isLoading} />
      </div>

      {/* Recent Documents */}
      <RecentDocuments documents={recent.data ?? []} loading={recent.isLoading} />
    </div>
  );
}
