import { useState } from "react";
import MainLayout from "../../layouts/MainLayout";
import { useAuth } from "../../contexts/AuthContext";
import { useLanguage } from "../../contexts/LanguageContext";
import { LANGUAGES } from "../../utils/i18n";
import { apiErrorMessage } from "../../services/api";

export default function Profile() {
  const { user, updateProfile } = useAuth();
  const { t, setLanguage } = useLanguage();

  const [fullName, setFullName] = useState(user?.full_name || "");
  const [phone, setPhone] = useState(user?.phone || "");
  const [preferredLanguage, setPreferredLanguage] = useState(user?.preferred_language || "en");
  const [status, setStatus] = useState("idle"); // idle | saving | done | error
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus("saving");
    setError("");
    try {
      await updateProfile({ full_name: fullName, phone, preferred_language: preferredLanguage });
      setLanguage(preferredLanguage);
      setStatus("done");
    } catch (err) {
      setStatus("error");
      setError(apiErrorMessage(err));
    }
  };

  return (
    <MainLayout>
      <div className="max-w-sm mx-auto px-6 py-12">
        <h1 className="font-display text-2xl font-semibold text-ink mb-8">{t("profile")}</h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="field-label">{t("email")}</label>
            <input value={user?.email || ""} disabled className="field-input bg-ink/5 text-ink-faint" />
          </div>
          <div>
            <label className="field-label" htmlFor="fullName">{t("fullName")}</label>
            <input id="fullName" value={fullName} onChange={(e) => setFullName(e.target.value)} className="field-input" />
          </div>
          <div>
            <label className="field-label" htmlFor="phone">{t("phone")}</label>
            <input id="phone" value={phone} onChange={(e) => setPhone(e.target.value)} className="field-input" />
          </div>
          <div>
            <label className="field-label" htmlFor="preferredLanguage">{t("language")}</label>
            <select
              id="preferredLanguage" value={preferredLanguage}
              onChange={(e) => setPreferredLanguage(e.target.value)} className="field-input"
            >
              {LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>{l.label}</option>
              ))}
            </select>
          </div>

          {status === "done" && <p className="text-sm text-stamp-teal">Saved.</p>}
          {status === "error" && <p className="text-sm text-stamp-red">{error}</p>}

          <button type="submit" disabled={status === "saving"} className="btn-primary w-full">
            {status === "saving" ? "…" : "Save"}
          </button>
        </form>
      </div>
    </MainLayout>
  );
}
