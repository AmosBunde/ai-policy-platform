import { useParams } from "react-router-dom";
import { Card } from "../components/ui/Card";

export default function DocumentDetail() {
  const { id } = useParams<{ id: string }>();
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Document Detail</h1>
      <Card><p className="text-slate-500">Document ID: {id}</p></Card>
    </div>
  );
}
