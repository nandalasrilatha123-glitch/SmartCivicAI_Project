import { Link } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import ModuleCard from "../components/ModuleCard";
import { useLanguage } from "../contexts/LanguageContext";
import { useAuth } from "../contexts/AuthContext";

const MODULES = ["GOVERNMENT_SCHOOLS", "AGRICULTURE", "HEALTHCARE", "TRAFFIC"];

export default function LandingPage() {
  const { t } = useLanguage();
  const { isAuthenticated } = useAuth();

  return (
    <MainLayout>
      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 pt-16 pb-20 grid md:grid-cols-[1.2fr_0.8fr] gap-12 items-center">
        <div>
          <h1 className="font-display text-4xl md:text-5xl font-semibold text-ink leading-[1.15] max-w-xl">
            {t("tagline")}
          </h1>
          <p className="mt-5 text-ink-soft max-w-md leading-relaxed">{t("heroSub")}</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to={isAuthenticated ? "/complaints/new" : "/register"} className="btn-accent">
              {t("reportAnIssue")}
            </Link>
            <Link to={isAuthenticated ? "/dashboard" : "/login"} className="btn-secondary">
              {t("trackComplaint")}
            </Link>
          </div>
        </div>

        {/* Hero visual: a sample complaint token/stamp, grounding the design
            in the product's actual mechanic rather than a generic graphic */}
        <div className="justify-self-center md:justify-self-end">
          <div className="bg-paper-raised border border-ink/15 p-6 w-72 relative">
            <div className="absolute -top-3 left-6 bg-marigold text-ink text-xs font-semibold px-3 py-1">
              {t("complaintNumber")}
            </div>
            <p className="font-mono text-lg text-ink mt-3 tracking-wide">SCH-2026-000114</p>
            <div className="mt-4 border-t border-dashed border-ink/20 pt-4 space-y-2 text-sm text-ink-soft">
              <p>{t("schools")} · {t("category")}: Mid-day meal</p>
              <p>{t("submittedOn")}: 12 Aug 2026</p>
            </div>
            <div className="mt-5">
              <span className="stamp border-stamp-teal text-stamp-teal">{t("statusValues.RESOLVED")}</span>
            </div>
          </div>
        </div>
      </section>

      {/* Modules */}
      <section className="max-w-6xl mx-auto px-6 pb-20">
        <h2 className="font-display text-2xl font-semibold text-ink mb-6">{t("fourDepartments")}</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {MODULES.map((code) => (
            <Link key={code} to={isAuthenticated ? "/complaints/new" : "/login"} className="block">
              <ModuleCard code={code} as="div" />
            </Link>
          ))}
        </div>
      </section>

      {/* How it works — a genuine sequence, so numbering here is earned */}
      <section className="bg-ink text-paper py-16">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="font-display text-2xl font-semibold mb-10">{t("howItWorks")}</h2>
          <div className="grid md:grid-cols-4 gap-8">
            {[1, 2, 3, 4].map((n) => (
              <div key={n} className="flex flex-col gap-2">
                <span className="font-display text-3xl text-marigold">{n}</span>
                <h3 className="font-semibold">{t(`step${n}`)}</h3>
                <p className="text-sm text-paper/70 leading-relaxed">{t(`step${n}Sub`)}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </MainLayout>
  );
}
