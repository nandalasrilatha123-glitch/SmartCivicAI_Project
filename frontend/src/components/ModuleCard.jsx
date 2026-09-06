import { useLanguage } from "../contexts/LanguageContext";
import { MODULE_COLORS, MODULE_LABEL_KEYS } from "../utils/statusMeta";

const ICONS = {
  GOVERNMENT_SCHOOLS: (
    <path d="M3 10.5 12 5l9 5.5-9 5.5-9-5.5Z M6 12.5V17c0 .8 2.5 2.5 6 2.5s6-1.7 6-2.5v-4.5" />
  ),
  AGRICULTURE: <path d="M12 21V9 M12 9c0-3 2-5 5-5 0 3-2 5-5 5Z M12 13c0-3-2-5-5-5 0 3 2 5 5 5Z" />,
  HEALTHCARE: <path d="M12 4v16 M4 12h16 M6 4h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Z" />,
  TRAFFIC: <path d="M12 3v3 M12 18v3 M6 8h12l-1.5 10h-9L6 8Z M9 12h6" />,
};

export default function ModuleCard({ code, onClick, selected = false, as = "button" }) {
  const { t } = useLanguage();
  const color = MODULE_COLORS[code];
  const Comp = as;

  return (
    <Comp
      type={as === "button" ? "button" : undefined}
      onClick={onClick}
      style={{ "--plaque-color": color }}
      className={`plaque text-left w-full ${selected ? "bg-white ring-2 ring-marigold ring-offset-1" : ""}`}
    >
      <svg viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" className="w-7 h-7 mb-2">
        {ICONS[code]}
      </svg>
      <span className="font-display text-lg font-semibold text-ink">{t(MODULE_LABEL_KEYS[code])}</span>
    </Comp>
  );
}
