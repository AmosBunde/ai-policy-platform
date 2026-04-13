import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Shield } from "lucide-react";
import { useAuthStore } from "../store/authStore";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Card } from "../components/ui/Card";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const login = useAuthStore((s) => s.login);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/");
    } catch {
      setError("Invalid credentials");
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
          <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <Input label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required error={error} />
          <Button type="submit" className="w-full" loading={loading}>Sign In</Button>
        </form>
        <p className="text-center text-sm text-slate-500 mt-4">
          No account? <Link to="/register" className="text-accent hover:underline">Register</Link>
        </p>
      </Card>
    </div>
  );
}
