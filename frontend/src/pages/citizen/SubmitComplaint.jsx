import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import MainLayout from "../../layouts/MainLayout";
import ModuleCard from "../../components/ModuleCard";
import LoadingSpinner from "../../components/LoadingSpinner";
import { useLanguage } from "../../contexts/LanguageContext";
import { LANGUAGES } from "../../utils/i18n";
import { listModules } from "../../services/catalogService";
import { submitComplaint } from "../../services/complaintService";
import { apiErrorMessage } from "../../services/api";

const MODULES = ["GOVERNMENT_SCHOOLS", "AGRICULTURE", "HEALTHCARE", "TRAFFIC"];

export default function SubmitComplaint() {
  const { t, language } = useLanguage();
  const navigate = useNavigate();

  const [modules, setModules] = useState([]);
  const [isLoadingModules, setIsLoadingModules] = useState(true);

  const [selectedModule, setSelectedModule] = useState(null);
  const [categoryId, setCategoryId] = useState("");
  const [description, setDescription] = useState("");
  const [originalLanguage, setOriginalLanguage] = useState(language);
  const [latitude, setLatitude] = useState(null);
  const [longitude, setLongitude] = useState(null);
  const [address, setAddress] = useState("");
  const [image, setImage] = useState(null);
  const [locationStatus, setLocationStatus] = useState("idle"); // idle | locating | done | error

  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    listModules().then(setModules).finally(() => setIsLoadingModules(false));
  }, []);

  const currentModuleData = modules.find((m) => m.code === selectedModule);

  const handleUseLocation = () => {
    if (!navigator.geolocation) {
      setLocationStatus("error");
      return;
    }
    setLocationStatus("locating");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLatitude(pos.coords.latitude);
        setLongitude(pos.coords.longitude);
        setLocationStatus("done");
      },
      () => setLocationStatus("error"),
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!selectedModule) {
      setError(t("module") + " " + t("required"));
      return;
    }
    if (description.trim().length < 10) {
      setError("Please describe the issue in a bit more detail (at least 10 characters).");
      return;
    }

    setIsSubmitting(true);
    try {
      const complaint = await submitComplaint({
        module: selectedModule,
        categoryId: categoryId || undefined,
        description,
        originalLanguage,
        latitude,
        longitude,
        address,
        image,
      });
      navigate(`/complaints/${complaint.id}`, { replace: true });
    } catch (err) {
      setError(apiErrorMessage(err, "Could not submit your complaint. Please try again."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <MainLayout>
      <div className="max-w-2xl mx-auto px-6 py-12">
        <h1 className="font-display text-2xl font-semibold text-ink mb-8">{t("reportAnIssue")}</h1>

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Module selection */}
          <div>
            <label className="field-label">{t("module")}</label>
            {isLoadingModules ? (
              <LoadingSpinner />
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {MODULES.map((code) => (
                  <ModuleCard
                    key={code}
                    code={code}
                    selected={selectedModule === code}
                    onClick={() => {
                      setSelectedModule(code);
                      setCategoryId("");
                    }}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Category */}
          <div>
            <label className="field-label" htmlFor="category">{t("category")}</label>
            <select
              id="category" value={categoryId} onChange={(e) => setCategoryId(e.target.value)}
              className="field-input" disabled={!selectedModule}
            >
              <option value="">{selectedModule ? "—" : t("selectModuleFirst")}</option>
              {currentModuleData?.categories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {language === "te" ? cat.name_te : language === "hi" ? cat.name_hi : cat.name_en}
                </option>
              ))}
            </select>
          </div>

          {/* Description */}
          <div>
            <label className="field-label" htmlFor="description">{t("description")}</label>
            <textarea
              id="description" required rows={5} value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder={t("descriptionPlaceholder")}
              className="field-input resize-none"
            />
          </div>

          {/* Language */}
          <div>
            <label className="field-label" htmlFor="originalLanguage">{t("language")}</label>
            <select
              id="originalLanguage" value={originalLanguage}
              onChange={(e) => setOriginalLanguage(e.target.value)} className="field-input"
            >
              {LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>{l.label}</option>
              ))}
            </select>
          </div>

          {/* Location */}
          <div>
            <label className="field-label">{t("location")}</label>
            <div className="flex items-center gap-3 mb-3">
              <button type="button" onClick={handleUseLocation} className="btn-secondary text-sm py-2 px-4">
                {locationStatus === "locating" ? "…" : t("useMyLocation")}
              </button>
              {locationStatus === "done" && (
                <span className="text-sm text-stamp-teal">
                  {latitude?.toFixed(4)}, {longitude?.toFixed(4)}
                </span>
              )}
              {locationStatus === "error" && (
                <span className="text-sm text-stamp-red">Could not get your location — you can still add an address below.</span>
              )}
            </div>
            <input
              value={address} onChange={(e) => setAddress(e.target.value)}
              placeholder={t("address")} className="field-input"
            />
          </div>

          {/* Image */}
          <div>
            <label className="field-label" htmlFor="image">{t("attachPhoto")}</label>
            <input
              id="image" type="file" accept="image/jpeg,image/png,image/webp"
              onChange={(e) => setImage(e.target.files?.[0] || null)}
              className="block w-full text-sm text-ink-soft file:mr-4 file:py-2 file:px-4 file:border file:border-ink/30 file:bg-white file:text-sm file:font-medium hover:file:border-ink"
            />
          </div>

          {error && <p className="text-sm text-stamp-red">{error}</p>}

          <button type="submit" disabled={isSubmitting} className="btn-primary w-full">
            {isSubmitting ? t("submitting") : t("submitComplaint")}
          </button>
        </form>
      </div>
    </MainLayout>
  );
}
