import { createContext, useContext, useMemo, useState } from "react";
import { t as translate } from "../utils/i18n";

const LanguageContext = createContext(null);

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(() => localStorage.getItem("scai_language") || "en");

  const setLanguage = (lang) => {
    localStorage.setItem("scai_language", lang);
    setLanguageState(lang);
  };

  const value = useMemo(
    () => ({
      language,
      setLanguage,
      t: (key) => translate(language, key),
    }),
    [language]
  );

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLanguage must be used within a LanguageProvider");
  return ctx;
}
