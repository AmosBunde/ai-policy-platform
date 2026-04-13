import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Shield } from "lucide-react";
import { useLogin } from "../hooks/useAuth";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Card } from "../components/ui/Card";

const loginSchema = z.object({
  email: z.string().min(1, "Email is required").email("Invalid email format"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

type LoginForm = z.infer<typeof loginSchema>;

export default function Login() {
  const [searchParams] = useSearchParams();
  const returnUrl = searchParams.get("returnUrl") || "/";
  const loginMutation = useLogin(returnUrl);
  const [rateLimitSeconds, setRateLimitSeconds] = useState(0);

  const { register, handleSubmit, formState: { errors } } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginForm) => {
    if (rateLimitSeconds > 0) return;

    try {
      await loginMutation.mutateAsync(data);
    } catch (err: unknown) {
      // Handle 429 rate limit
      if (isAxiosError(err) && err.response?.status === 429) {
        const retryAfter = Number(err.response.headers["retry-after"]) || 30;
        setRateLimitSeconds(retryAfter);
        const interval = setInterval(() => {
          setRateLimitSeconds((s) => {
            if (s <= 1) {
              clearInterval(interval);
              return 0;
            }
            return s - 1;
          });
        }, 1000);
      }
    }
  };

  const errorMessage = loginMutation.isError && rateLimitSeconds === 0
    ? "Invalid credentials"
    : null;

  return (
    <div className="min-h-screen flex items-center justify-center bg-navy-900 px-4">
      <Card className="w-full max-w-md">
        <div className="flex items-center gap-2 justify-center mb-6">
          <Shield className="h-8 w-8 text-accent" />
          <span className="text-2xl font-bold text-navy-900 dark:text-white">RegulatorAI</span>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input
            label="Email"
            type="email"
            autoComplete="email"
            error={errors.email?.message}
            {...register("email")}
          />
          <Input
            label="Password"
            type="password"
            autoComplete="off"
            error={errors.password?.message}
            {...register("password")}
          />

          <div className="flex items-center justify-between">
            <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
              <input type="checkbox" className="rounded border-slate-300" />
              Remember me
            </label>
            <Link to="/forgot-password" className="text-sm text-accent hover:underline">
              Forgot password?
            </Link>
          </div>

          {errorMessage && (
            <p className="text-sm text-danger text-center" role="alert">{errorMessage}</p>
          )}

          {rateLimitSeconds > 0 && (
            <p className="text-sm text-accent text-center" role="alert">
              Too many attempts. Try again in {rateLimitSeconds} seconds.
            </p>
          )}

          <Button
            type="submit"
            className="w-full"
            loading={loginMutation.isPending}
            disabled={rateLimitSeconds > 0}
          >
            {rateLimitSeconds > 0 ? `Wait ${rateLimitSeconds}s` : "Sign In"}
          </Button>
        </form>

        <p className="text-center text-sm text-slate-500 mt-4">
          No account?{" "}
          <Link to="/register" className="text-accent hover:underline">Register</Link>
        </p>
      </Card>
    </div>
  );
}

function isAxiosError(err: unknown): err is { response?: { status: number; headers: Record<string, string> } } {
  return typeof err === "object" && err !== null && "response" in err;
}
