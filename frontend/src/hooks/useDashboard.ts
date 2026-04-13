import { useQuery } from "@tanstack/react-query";
import { api } from "../services/api";

interface DashboardKPIs {
  totalDocuments: number;
  pendingReviews: number;
  highUrgency: number;
  reportsGenerated: number;
  documentsTrend: "up" | "down" | "neutral";
  documentsTrendLabel: string;
  pendingTrend: "up" | "down" | "neutral";
  pendingTrendLabel: string;
  urgencyTrend: "up" | "down" | "neutral";
  urgencyTrendLabel: string;
  reportsTrend: "up" | "down" | "neutral";
  reportsTrendLabel: string;
}

interface ActivityDataPoint {
  date: string;
  documents: number;
  enriched: number;
}

interface HeatmapCell {
  region: string;
  category: string;
  score: number;
}

interface RecentDocument {
  id: string;
  title: string;
  jurisdiction: string;
  urgencyLevel: string;
  status: string;
  createdAt: string;
}

// Sample data used when API is unavailable (development/demo)
const SAMPLE_KPIS: DashboardKPIs = {
  totalDocuments: 1247,
  pendingReviews: 23,
  highUrgency: 8,
  reportsGenerated: 89,
  documentsTrend: "up",
  documentsTrendLabel: "+12 today",
  pendingTrend: "down",
  pendingTrendLabel: "-3 from yesterday",
  urgencyTrend: "up",
  urgencyTrendLabel: "+2 this week",
  reportsTrend: "up",
  reportsTrendLabel: "+5 this month",
};

const SAMPLE_ACTIVITY: ActivityDataPoint[] = Array.from({ length: 30 }, (_, i) => {
  const date = new Date();
  date.setDate(date.getDate() - (29 - i));
  return {
    date: `${date.getMonth() + 1}/${date.getDate()}`,
    documents: Math.floor(Math.random() * 20) + 5,
    enriched: Math.floor(Math.random() * 15) + 3,
  };
});

const SAMPLE_HEATMAP: HeatmapCell[] = [
  { region: "EU", category: "privacy", score: 9 },
  { region: "EU", category: "safety", score: 8 },
  { region: "EU", category: "transparency", score: 7 },
  { region: "US-Federal", category: "safety", score: 6 },
  { region: "US-Federal", category: "IP", score: 4 },
  { region: "UK", category: "privacy", score: 7 },
  { region: "UK", category: "liability", score: 5 },
  { region: "APAC", category: "safety", score: 3 },
  { region: "Canada", category: "privacy", score: 5 },
  { region: "LatAm", category: "antitrust", score: 2 },
];

const SAMPLE_RECENT: RecentDocument[] = [
  { id: "1", title: "EU AI Act - Final Implementation Guidelines", jurisdiction: "EU", urgencyLevel: "critical", status: "enriched", createdAt: new Date(Date.now() - 3600000).toISOString() },
  { id: "2", title: "NIST AI Risk Management Framework Update", jurisdiction: "US-Federal", urgencyLevel: "high", status: "enriched", createdAt: new Date(Date.now() - 7200000).toISOString() },
  { id: "3", title: "UK ICO Guidance on AI and Data Protection", jurisdiction: "UK", urgencyLevel: "normal", status: "processing", createdAt: new Date(Date.now() - 14400000).toISOString() },
  { id: "4", title: "Canada AIDA Bill Second Reading", jurisdiction: "Canada", urgencyLevel: "normal", status: "ingested", createdAt: new Date(Date.now() - 28800000).toISOString() },
  { id: "5", title: "Singapore AI Governance Framework v2", jurisdiction: "APAC", urgencyLevel: "low", status: "enriched", createdAt: new Date(Date.now() - 86400000).toISOString() },
];

export function useDashboardKPIs(refetchInterval: number | false = 30_000) {
  return useQuery({
    queryKey: ["dashboard", "kpis"],
    queryFn: async () => {
      try {
        const resp = await api.get("/dashboard/kpis");
        return resp.data as DashboardKPIs;
      } catch {
        return SAMPLE_KPIS;
      }
    },
    refetchInterval,
    placeholderData: SAMPLE_KPIS,
  });
}

export function useDashboardActivity(refetchInterval: number | false = 30_000) {
  return useQuery({
    queryKey: ["dashboard", "activity"],
    queryFn: async () => {
      try {
        const resp = await api.get("/dashboard/activity");
        return resp.data as ActivityDataPoint[];
      } catch {
        return SAMPLE_ACTIVITY;
      }
    },
    refetchInterval,
    placeholderData: SAMPLE_ACTIVITY,
  });
}

export function useDashboardHeatmap(refetchInterval: number | false = 30_000) {
  return useQuery({
    queryKey: ["dashboard", "heatmap"],
    queryFn: async () => {
      try {
        const resp = await api.get("/dashboard/heatmap");
        return resp.data as HeatmapCell[];
      } catch {
        return SAMPLE_HEATMAP;
      }
    },
    refetchInterval,
    placeholderData: SAMPLE_HEATMAP,
  });
}

export function useRecentDocuments(refetchInterval: number | false = 30_000) {
  return useQuery({
    queryKey: ["dashboard", "recent-documents"],
    queryFn: async () => {
      try {
        const resp = await api.get("/dashboard/recent-documents");
        return resp.data as RecentDocument[];
      } catch {
        return SAMPLE_RECENT;
      }
    },
    refetchInterval,
    placeholderData: SAMPLE_RECENT,
  });
}
