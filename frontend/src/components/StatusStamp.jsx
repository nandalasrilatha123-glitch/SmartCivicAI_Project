import { useLanguage } from "../contexts/LanguageContext";
import { STATUS_COLORS } from "../utils/statusMeta";

export default function StatusStamp({ status }) {
  const { t } = useLanguage();
  const colors = STATUS_COLORS[status] || STATUS_COLORS.NEW;

  return (
    <span className={`stamp ${colors.border} ${colors.text}`}>
      {t(`statusValues.${status}`)}
    </span>
  );
}
