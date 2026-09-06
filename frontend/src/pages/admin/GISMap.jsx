import { useEffect, useState } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet";
import AdminLayout from "../../layouts/AdminLayout";
import LoadingSpinner from "../../components/LoadingSpinner";
import { getHotspots } from "../../services/analyticsService";
import { MODULE_COLORS } from "../../utils/statusMeta";

const MODULES = ["GOVERNMENT_SCHOOLS", "AGRICULTURE", "HEALTHCARE", "TRAFFIC"];
const HYDERABAD = [17.385, 78.4867];

export default function GISMap() {
  const [module, setModule] = useState("");
  const [hotspots, setHotspots] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getHotspots(module ? { module } : {}).then(setHotspots).finally(() => setLoading(false));
  }, [module]);

  const maxCount = Math.max(1, ...hotspots.map((h) => h.count));

  return (
    <AdminLayout>
      <div className="p-8">
        <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
          <div>
            <h1 className="font-display text-2xl font-semibold text-ink">Complaint Hotspot Map</h1>
            <p className="text-xs text-ink-faint mt-1">
              OpenStreetMap tiles (no Google Maps API key configured — set GOOGLE_MAPS_API_KEY in the backend .env
              and wire it here to switch providers; see spec §12 fallback requirement).
            </p>
          </div>
          <select value={module} onChange={(e) => setModule(e.target.value)} className="field-input w-56">
            <option value="">All modules</option>
            {MODULES.map((m) => <option key={m} value={m}>{m.replace("_", " ")}</option>)}
          </select>
        </div>

        {loading ? (
          <LoadingSpinner />
        ) : (
          <div className="border border-ink/10" style={{ height: "70vh" }}>
            <MapContainer center={HYDERABAD} zoom={11} style={{ height: "100%", width: "100%" }}>
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {hotspots.map((h, i) => (
                <CircleMarker
                  key={i}
                  center={[h.latitude, h.longitude]}
                  radius={8 + (h.count / maxCount) * 20}
                  pathOptions={{
                    color: MODULE_COLORS[h.dominant_module] || "#1B2A4A",
                    fillColor: MODULE_COLORS[h.dominant_module] || "#1B2A4A",
                    fillOpacity: 0.45,
                    weight: 2,
                  }}
                >
                  <Popup>
                    <div className="text-sm">
                      <p className="font-semibold">{h.count} complaints</p>
                      <p>{h.dominant_module.replace("_", " ")}</p>
                      <p>Dominant priority: {h.dominant_priority}</p>
                    </div>
                  </Popup>
                </CircleMarker>
              ))}
            </MapContainer>
          </div>
        )}
      </div>
    </AdminLayout>
  );
}
