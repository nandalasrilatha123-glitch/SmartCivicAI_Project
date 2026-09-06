import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import { LANGUAGES } from "../utils/i18n";
import { apiErrorMessage } from "../services/api";

export default function RegisterPage() {
  const { register } = useAuth();
  const { t, language } = useLanguage();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    fullName: "", email: "", phone: "", password: "", confirmPassword: "", preferredLanguage: language,
  });
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (form.password !== form.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setIsSubmitting(true);
    try {
      await register(form);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(apiErrorMessage(err, "Could not create your account."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <MainLayout>
      <div className="max-w-sm mx-auto px-6 py-16">
        <h1 className="font-display text-2xl font-semibold text-ink mb-6">{t("createAccount")}</h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="field-label" htmlFor="fullName">{t("fullName")}</label>
            <input id="fullName" required value={form.fullName} onChange={update("fullName")} className="field-input" />
          </div>
          <div>
            <label className="field-label" htmlFor="email">{t("email")}</label>
            <input id="email" type="email" required value={form.email} onChange={update("email")} className="field-input" autoComplete="email" />
          </div>
          <div>
            <label className="field-label" htmlFor="phone">{t("phone")}</label>
            <input id="phone" value={form.phone} onChange={update("phone")} className="field-input" />
          </div>
          <div>
            <label className="field-label" htmlFor="preferredLanguage">{t("language")}</label>
            <select
              id="preferredLanguage" value={form.preferredLanguage}
              onChange={update("preferredLanguage")} className="field-input"
            >
              {LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>{l.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="field-label" htmlFor="password">{t("password")}</label>
            <input
              id="password" type="password" required minLength={8} value={form.password}
              onChange={update("password")} className="field-input" autoComplete="new-password"
            />
          </div>
          <div>
            <label className="field-label" htmlFor="confirmPassword">{t("confirmPassword")}</label>
            <input
              id="confirmPassword" type="password" required value={form.confirmPassword}
              onChange={update("confirmPassword")} className="field-input" autoComplete="new-password"
            />
          </div>

          {error && <p className="text-sm text-stamp-red">{error}</p>}

          <button type="submit" disabled={isSubmitting} className="btn-primary w-full">
            {isSubmitting ? "..." : t("createAccount")}
          </button>
        </form>

        <p className="mt-6 text-sm text-ink-soft">
          {t("alreadyHaveAccount")}{" "}
          <Link to="/login" className="text-ink font-medium underline underline-offset-2">
            {t("login")}
          </Link>
        </p>
      </div>
    </MainLayout>
  );
}
