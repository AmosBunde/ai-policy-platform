import { useState } from "react";
import { Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Shield, CheckCircle2 } from "lucide-react";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Card } from "../components/ui/Card";
import { api } from "../services/api";

const forgotSchema = z.object({
  email: z.string().min(1, "Email is required").email("Invalid email format"),
});

type ForgotForm = z.infer<typeof forgotSchema>;

export default function ForgotPassword() {
  // SECURITY: Always show success regardless of whether email exists (anti-enumeration)
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const { register, handleSubmit, formState: { errors } } = useForm<ForgotForm>({
    resolver: zodResolver(forgotSchema),
  });

  const onSubmit = async (_data: ForgotForm) => {
    setLoading(true);
    try {
      // Fire and forget — always show success
      await api.post("/auth/forgot-password", _data).catch(() => {});
    } finally {
      setLoading(false);
      setSubmitted(true);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-navy-900 px-4">
      <Card className="w-full max-w-md">
        <div className="flex items-center gap-2 justify-center mb-6">
          <Shield className="h-8 w-8 text-accent" />
          <span className="text-2xl font-bold text-navy-900 dark:text-white">RegulatorAI</span>
        </div>

        {submitted ? (
          <div className="text-center space-y-4">
            <CheckCircle2 className="h-12 w-12 text-success mx-auto" />
            <h2 className="text-lg font-semibold">Check your email</h2>
            <p className="text-sm text-slate-500">
              If an account with that email exists, we have sent password reset instructions.
            </p>
            <Link to="/login" className="text-accent hover:underline text-sm">
              Return to Sign In
            </Link>
          </div>
        ) : (
          <>
            <h2 className="text-lg font-semibold text-center mb-2">Reset Password</h2>
            <p className="text-sm text-slate-500 text-center mb-4">
              Enter your email address and we will send you reset instructions.
            </p>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <Input
                label="Email"
                type="email"
                autoComplete="email"
                error={errors.email?.message}
                {...register("email")}
              />
              <Button type="submit" className="w-full" loading={loading}>
                Send Reset Link
              </Button>
            </form>
            <p className="text-center text-sm text-slate-500 mt-4">
              <Link to="/login" className="text-accent hover:underline">Back to Sign In</Link>
            </p>
          </>
        )}
      </Card>
    </div>
  );
}
