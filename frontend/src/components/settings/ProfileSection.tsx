import { useState } from "react";
import { Save } from "lucide-react";
import { Card } from "../ui/Card";
import { Input } from "../ui/Input";
import { Button } from "../ui/Button";
import { Toast } from "../ui/Toast";
import { PasswordStrengthBar } from "../auth/PasswordStrengthBar";
import { useAuthStore } from "../../store/authStore";

export function ProfileSection() {
  const user = useAuthStore((s) => s.user);

  const [fullName, setFullName] = useState(user?.fullName ?? "");
  const [organization, setOrganization] = useState(user?.organization ?? "");

  // Password change
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordErrors, setPasswordErrors] = useState<Record<string, string>>({});
  const [toast, setToast] = useState<{ message: string; variant: "success" | "error" } | null>(null);

  const handleProfileSave = () => {
    setToast({ message: "Profile updated successfully.", variant: "success" });
  };

  const handlePasswordChange = () => {
    const errors: Record<string, string> = {};

    if (!currentPassword) {
      errors.currentPassword = "Current password is required";
    }
    if (!newPassword) {
      errors.newPassword = "New password is required";
    } else if (newPassword.length < 8) {
      errors.newPassword = "Password must be at least 8 characters";
    }
    if (newPassword !== confirmPassword) {
      errors.confirmPassword = "Passwords do not match";
    }

    setPasswordErrors(errors);
    if (Object.keys(errors).length > 0) return;

    // In production, this would call the API
    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
    setPasswordErrors({});
    setToast({ message: "Password changed successfully.", variant: "success" });
  };

  return (
    <div className="space-y-6">
      {/* Toast */}
      {toast && (
        <div className="fixed top-4 right-4 z-50">
          <Toast message={toast.message} variant={toast.variant} onClose={() => setToast(null)} />
        </div>
      )}

      {/* Profile info */}
      <Card>
        <h3 className="text-lg font-semibold mb-4">Profile Information</h3>
        <div className="space-y-4 max-w-md">
          <Input
            label="Full Name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
          <Input
            label="Email"
            value={user?.email ?? ""}
            disabled
            helperText="Email cannot be changed."
          />
          <Input
            label="Organization"
            value={organization}
            onChange={(e) => setOrganization(e.target.value)}
            placeholder="Your organization"
          />
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-500">Role:</span>
            <span className="text-sm font-medium capitalize">{user?.role}</span>
          </div>
          <Button size="sm" onClick={handleProfileSave}>
            <Save className="h-4 w-4" /> Save Profile
          </Button>
        </div>
      </Card>

      {/* Password change */}
      <Card>
        <h3 className="text-lg font-semibold mb-4">Change Password</h3>
        <div className="space-y-4 max-w-md">
          <Input
            label="Current Password"
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            error={passwordErrors.currentPassword}
            autoComplete="current-password"
          />
          <div className="space-y-1">
            <Input
              label="New Password"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              error={passwordErrors.newPassword}
              autoComplete="new-password"
            />
            <PasswordStrengthBar password={newPassword} />
          </div>
          <Input
            label="Confirm New Password"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            error={passwordErrors.confirmPassword}
            autoComplete="new-password"
          />
          <Button size="sm" onClick={handlePasswordChange}>
            Change Password
          </Button>
        </div>
      </Card>
    </div>
  );
}
