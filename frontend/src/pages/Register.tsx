import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Shield } from "lucide-react";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Card } from "../components/ui/Card";
import { api } from "../services/api";

export default function Register() {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.post("/auth/register", { email, password, full_name: fullName });
      navigate("/login");
    } catch {
      setError("Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-navy-900 px-4">
      <Card className="w-full max-w-md">
        <div className="flex items-center gap-2 justify-center mb-6">
          <Shield className="h-8 w-8 text-accent" />
          <span className="text-2xl font-bold text-navy-900 dark:text-white">RegulatorAI</span>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label="Full Name" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
          <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <Input label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required helperText="Min 8 chars, mixed case + digit" error={error} />
          <Button type="submit" className="w-full" loading={loading}>Create Account</Button>
        </form>
        <p className="text-center text-sm text-slate-500 mt-4">
          Already registered? <Link to="/login" className="text-accent hover:underline">Sign In</Link>
        </p>
      </Card>
    </div>
  );
}
