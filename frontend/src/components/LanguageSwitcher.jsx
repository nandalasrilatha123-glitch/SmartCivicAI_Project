import { LANGUAGES } from "../utils/i18n";
import { useLanguage } from "../contexts/LanguageContext";

export default function LanguageSwitcher({ compact = false }) {
  const { language, setLanguage } = useLanguage();

  return (
    <div className={compact ? "flex items-center gap-1" : "flex items-center gap-1.5"}>
      {LANGUAGES.map((lang, idx) => (
        <span key={lang.code} className="flex items-center">
          <button
            type="button"
            onClick={() => setLanguage(lang.code)}
            aria-pressed={language === lang.code}
            className={`px-2 py-1 text-sm transition-colors ${
              language === lang.code ? "text-ink font-semibold underline underline-offset-4 decoration-marigold decoration-2" : "text-ink-faint hover:text-ink"
            }`}
          >
            {lang.label}
          </button>
          {idx < LANGUAGES.length - 1 && <span className="text-ink/20">|</span>}
        </span>
      ))}
    </div>
  );
}
