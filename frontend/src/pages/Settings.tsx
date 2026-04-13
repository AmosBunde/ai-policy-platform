import { Card } from "../components/ui/Card";
import { useAuthStore } from "../store/authStore";

export default function Settings() {
  const user = useAuthStore((s) => s.user);
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>
      <Card>
        <h2 className="text-lg font-semibold mb-4">Profile</h2>
        <dl className="space-y-2 text-sm">
          <div className="flex"><dt className="w-32 text-slate-500">Name</dt><dd>{user?.fullName}</dd></div>
          <div className="flex"><dt className="w-32 text-slate-500">Email</dt><dd>{user?.email}</dd></div>
          <div className="flex"><dt className="w-32 text-slate-500">Role</dt><dd className="capitalize">{user?.role}</dd></div>
        </dl>
      </Card>
    </div>
  );
}
