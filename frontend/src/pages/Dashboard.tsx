import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";

export default function Dashboard() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <p className="text-sm text-slate-500">Documents Tracked</p>
          <p className="text-3xl font-bold mt-1">1,247</p>
          <Badge variant="success" className="mt-2">+12 today</Badge>
        </Card>
        <Card>
          <p className="text-sm text-slate-500">Pending Review</p>
          <p className="text-3xl font-bold mt-1">23</p>
          <Badge variant="warning" className="mt-2">5 critical</Badge>
        </Card>
        <Card>
          <p className="text-sm text-slate-500">Reports Generated</p>
          <p className="text-3xl font-bold mt-1">89</p>
          <Badge variant="info" className="mt-2">This month</Badge>
        </Card>
        <Card>
          <p className="text-sm text-slate-500">Active Watch Rules</p>
          <p className="text-3xl font-bold mt-1">15</p>
          <Badge className="mt-2">3 triggered today</Badge>
        </Card>
      </div>
    </div>
  );
}
