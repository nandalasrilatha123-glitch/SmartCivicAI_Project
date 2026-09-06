import { useLanguage } from "../contexts/LanguageContext";
import { PRIORITY_COLORS } from "../utils/statusMeta";

export default function PriorityBadge({ priority }) {
  const { t } = useLanguage();
  const classes = PRIORITY_COLORS[priority] || PRIORITY_COLORS.MEDIUM;

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 text-xs font-medium ${classes}`}>
      {t(`priorityValues.${priority}`)}
    </span>
  );
}
