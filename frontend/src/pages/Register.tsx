import { Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Shield } from "lucide-react";
import { useRegister } from "../hooks/useAuth";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Select } from "../components/ui/Select";
import { Card } from "../components/ui/Card";
import { PasswordStrengthBar } from "../components/auth/PasswordStrengthBar";

const registerSchema = z.object({
  full_name: z.string().min(2, "Name must be at least 2 characters").max(100, "Name too long"),
  email: z.string().min(1, "Email is required").email("Invalid email format"),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters")
    .max(128, "Password too long")
    .regex(/[a-z]/, "Must contain a lowercase letter")
    .regex(/[A-Z]/, "Must contain an uppercase letter")
    .regex(/\d/, "Must contain a digit"),
  confirmPassword: z.string(),
  organization: z.string().max(255).optional(),
  role: z.enum(["analyst", "viewer"]).default("analyst"),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"],
});

type RegisterForm = z.infer<typeof registerSchema>;

export default function Register() {
  const registerMutation = useRegister();

  const { register, handleSubmit, watch, formState: { errors } } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: { role: "analyst" },
  });

  const password = watch("password", "");

  const onSubmit = (data: RegisterForm) => {
    const { confirmPassword: _unused, ...payload } = data;
    registerMutation.mutate(payload);
  };

  const errorMessage = registerMutation.isError ? "Registration failed. Please try again." : null;

  return (
    <div className="min-h-screen flex items-center justify-center bg-navy-900 px-4 py-8">
      <Card className="w-full max-w-md">
        <div className="flex items-center gap-2 justify-center mb-6">
          <Shield className="h-8 w-8 text-accent" />
          <span className="text-2xl font-bold text-navy-900 dark:text-white">RegulatorAI</span>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input
            label="Full Name"
            autoComplete="name"
            error={errors.full_name?.message}
            {...register("full_name")}
          />
          <Input
            label="Email"
            type="email"
            autoComplete="email"
            error={errors.email?.message}
            {...register("email")}
          />
          <div className="space-y-1">
            <Input
              label="Password"
              type="password"
              autoComplete="off"
              error={errors.password?.message}
              {...register("password")}
            />
            <PasswordStrengthBar password={password} />
          </div>
          <Input
            label="Confirm Password"
            type="password"
            autoComplete="off"
            error={errors.confirmPassword?.message}
            {...register("confirmPassword")}
          />
          <Input
            label="Organization (optional)"
            autoComplete="organization"
            error={errors.organization?.message}
            {...register("organization")}
          />
          <Select
            label="Role"
            options={[
              { value: "analyst", label: "Analyst" },
              { value: "viewer", label: "Viewer" },
            ]}
            {...register("role")}
          />

          <div className="text-xs text-slate-500 space-y-0.5">
            <p>Password requirements:</p>
            <ul className="list-disc list-inside">
              <li>At least 8 characters</li>
              <li>At least one uppercase and one lowercase letter</li>
              <li>At least one digit</li>
            </ul>
          </div>

          {errorMessage && (
            <p className="text-sm text-danger text-center" role="alert">{errorMessage}</p>
          )}

          <Button
            type="submit"
            className="w-full"
            loading={registerMutation.isPending}
          >
            Create Account
          </Button>
        </form>

        <p className="text-center text-sm text-slate-500 mt-4">
          Already registered?{" "}
          <Link to="/login" className="text-accent hover:underline">Sign In</Link>
        </p>
      </Card>
    </div>
  );
}
