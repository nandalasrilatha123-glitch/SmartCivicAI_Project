import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import { apiErrorMessage } from "../services/api";

export default function LoginPage() {
  const { login } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const redirectTo = location.state?.from?.pathname || null;

  const roleHome = (role) => (role === "ADMIN" ? "/admin/dashboard" : role === "OFFICER" ? "/officer/dashboard" : "/dashboard");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setIsSubmitting(true);
    try {
      const user = await login({ email, password });
      navigate(redirectTo || roleHome(user.role), { replace: true });
    } catch (err) {
      setError(apiErrorMessage(err, "Incorrect email or password."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <MainLayout>
      <div className="max-w-sm mx-auto px-6 py-16">
        <h1 className="font-display text-2xl font-semibold text-ink mb-6">{t("login")}</h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="field-label" htmlFor="email">{t("email")}</label>
            <input
              id="email" type="email" required value={email}
              onChange={(e) => setEmail(e.target.value)} className="field-input"
              autoComplete="email"
            />
          </div>
          <div>
            <label className="field-label" htmlFor="password">{t("password")}</label>
            <input
              id="password" type="password" required value={password}
              onChange={(e) => setPassword(e.target.value)} className="field-input"
              autoComplete="current-password"
            />
          </div>

          {error && <p className="text-sm text-stamp-red">{error}</p>}

          <button type="submit" disabled={isSubmitting} className="btn-primary w-full">
            {isSubmitting ? "..." : t("login")}
          </button>
        </form>

        <p className="mt-6 text-sm text-ink-soft">
          {t("dontHaveAccount")}{" "}
          <Link to="/register" className="text-ink font-medium underline underline-offset-2">
            {t("createAccount")}
          </Link>
        </p>
      </div>
    </MainLayout>
  );
}
