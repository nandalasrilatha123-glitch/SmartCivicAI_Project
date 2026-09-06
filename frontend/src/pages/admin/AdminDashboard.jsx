import { useEffect, useState } from "react";
import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import AdminLayout from "../../layouts/AdminLayout";
import ChartCard from "../../components/admin/ChartCard";
import StatCard from "../../components/admin/StatCard";
import LoadingSpinner from "../../components/LoadingSpinner";
import * as analytics from "../../services/analyticsService";
import {
  CATEGORICAL_PALETTE, MODULE_COLORS, MODULE_LABEL_KEYS, PRIORITY_HEX, STATUS_HEX,
} from "../../utils/statusMeta";

const MODULES = ["GOVERNMENT_SCHOOLS", "AGRICULTURE", "HEALTHCARE", "TRAFFIC"];
const STATUSES = ["NEW", "PENDING", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "REJECTED", "ESCALATED", "REQUIRES_ADMIN_REVIEW"];

function pivotModuleStatus(rows) {
  // rows: [{module, status, count}] -> [{module, NEW: n, PENDING: n, ...}]
  const byModule = {};
  for (const r of rows) {
    byModule[r.module] ||= { module: r.module };
    byModule[r.module][r.status] = r.count;
  }
  return MODULES.filter((m) => byModule[m]).map((m) => byModule[m]);
}

export default function AdminDashboard() {
  const [moduleFilter, setModuleFilter] = useState("");
  const [granularity, setGranularity] = useState("month");
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState({});

  useEffect(() => {
    const params = moduleFilter ? { module: moduleFilter } : {};
    setLoading(true);

    Promise.all([
      analytics.getOverview(params),
      analytics.getStatusDistribution(params),
      analytics.getByModule(),
      analytics.getOverTime({ ...params, granularity }),
      analytics.getModuleStatusMatrix(),
      analytics.getPriorityDistribution(params),
      analytics.getDepartmentPerformance(params),
      analytics.getResolutionTime(params),
      analytics.getCategoryDistribution(params),
      analytics.getLanguageDistribution(params),
      analytics.getAIClassificationStats(),
      analytics.getAIRoutingStats(),
      analytics.getHotspots(params),
      analytics.getPredictedVolume(params),
      analytics.getPredictedHotspots(params),
    ])
      .then(
        ([
          overview, statusDist, byModule, overTime, moduleStatus, priorityDist,
          deptPerf, resolutionTime, categoryDist, languageDist, aiClass, aiRouting,
          hotspots, predictedVolume, predictedHotspots,
        ]) => {
          setData({
            overview, statusDist, byModule, overTime, moduleStatus, priorityDist,
            deptPerf, resolutionTime, categoryDist, languageDist, aiClass, aiRouting,
            hotspots, predictedVolume, predictedHotspots,
          });
        }
      )
      .finally(() => setLoading(false));
  }, [moduleFilter, granularity]);

  const o = data.overview;

  return (
    <AdminLayout>
      <div className="p-8 max-w-[1400px]">
        <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
          <h1 className="font-display text-2xl font-semibold text-ink">Admin Dashboard</h1>
          <select value={moduleFilter} onChange={(e) => setModuleFilter(e.target.value)} className="field-input w-56">
            <option value="">All departments</option>
            {MODULES.map((m) => (
              <option key={m} value={m}>{m.replace("_", " ")}</option>
            ))}
          </select>
        </div>

        {loading || !o ? (
          <LoadingSpinner label="Loading dashboard..." />
        ) : (
          <div className="space-y-6">
            {/* Overview cards */}
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              <StatCard label="Total" value={o.total} accent />
              <StatCard label="New" value={o.new} />
              <StatCard label="Pending" value={o.pending} />
              <StatCard label="Assigned" value={o.assigned} />
              <StatCard label="In progress" value={o.in_progress} />
              <StatCard label="Resolved" value={o.resolved} />
              <StatCard label="Rejected" value={o.rejected} />
              <StatCard label="Escalated" value={o.escalated} />
              <StatCard label="Overdue (>7d)" value={o.overdue} />
              <StatCard label="High priority open" value={o.high_priority} />
            </div>

            {/* Charts 1 + 2: Status distribution / By module */}
            <div className="grid md:grid-cols-2 gap-4">
              <ChartCard title="Complaint status distribution">
                <ResponsiveContainer width="100%" height={260}>
                  <PieChart>
                    <Pie data={data.statusDist} dataKey="count" nameKey="label" innerRadius={55} outerRadius={90} paddingAngle={2}>
                      {data.statusDist.map((entry) => (
                        <Cell key={entry.label} fill={STATUS_HEX[entry.label] || "#7C86A0"} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                  </PieChart>
                </ResponsiveContainer>
              </ChartCard>

              <ChartCard title="Complaints by module">
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={data.byModule}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1B2A4A20" />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} tickFormatter={(v) => v.replace("_", " ")} />
                    <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                    <Tooltip />
                    <Bar dataKey="count">
                      {data.byModule.map((entry) => (
                        <Cell key={entry.label} fill={MODULE_COLORS[entry.label] || "#1B2A4A"} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>
            </div>

            {/* Chart 3: Over time */}
            <ChartCard
              title="Complaints over time"
              subtitle={
                <span className="inline-flex gap-2 mt-1">
                  {["day", "week", "month", "year"].map((g) => (
                    <button
                      key={g} onClick={() => setGranularity(g)}
                      className={`text-xs px-2 py-1 border ${granularity === g ? "border-ink bg-ink text-paper" : "border-ink/20 text-ink-soft"}`}
                    >
                      {g}
                    </button>
                  ))}
                </span>
              }
            >
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={data.overTime}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1B2A4A20" />
                  <XAxis dataKey="period" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                  <Tooltip />
                  <Line type="monotone" dataKey="count" stroke="#E8A33D" strokeWidth={2.5} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>

            {/* Chart 4: Module-wise status (stacked) + Chart 5: Priority distribution */}
            <div className="grid md:grid-cols-2 gap-4">
              <ChartCard title="Module-wise complaint status">
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={pivotModuleStatus(data.moduleStatus)}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1B2A4A20" />
                    <XAxis dataKey="module" tick={{ fontSize: 10 }} tickFormatter={(v) => v.replace("_", " ")} />
                    <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                    <Tooltip />
                    <Legend wrapperStyle={{ fontSize: 10 }} />
                    {STATUSES.map((s) => (
                      <Bar key={s} dataKey={s} stackId="status" fill={STATUS_HEX[s]} name={s.replace("_", " ")} />
                    ))}
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>

              <ChartCard title="Priority distribution">
                <ResponsiveContainer width="100%" height={280}>
                  <PieChart>
                    <Pie data={data.priorityDist} dataKey="count" nameKey="label" outerRadius={90} label={(e) => e.label}>
                      {data.priorityDist.map((entry) => (
                        <Cell key={entry.label} fill={PRIORITY_HEX[entry.label] || "#7C86A0"} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </ChartCard>
            </div>

            {/* Chart 6: Department performance */}
            <ChartCard title="Department performance" subtitle="Received vs resolved, with resolution rate">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-ink-faint border-b border-ink/10">
                      <th className="py-2 pr-4">Department</th>
                      <th className="py-2 pr-4">Module</th>
                      <th className="py-2 pr-4">Received</th>
                      <th className="py-2 pr-4">Resolved</th>
                      <th className="py-2 pr-4">Pending</th>
                      <th className="py-2 pr-4">Resolution rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.deptPerf.map((d) => (
                      <tr key={d.department_id} className="border-b border-dashed border-ink/10">
                        <td className="py-2 pr-4">{d.department_name}</td>
                        <td className="py-2 pr-4 text-ink-faint">{d.module.replace("_", " ")}</td>
                        <td className="py-2 pr-4">{d.received}</td>
                        <td className="py-2 pr-4">{d.resolved}</td>
                        <td className="py-2 pr-4">{d.pending}</td>
                        <td className="py-2 pr-4 font-medium">{d.resolution_rate}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </ChartCard>

            {/* Chart 7: Avg resolution time + Chart 9: Language distribution */}
            <div className="grid md:grid-cols-2 gap-4">
              <ChartCard title="Average resolution time" subtitle="Hours from submission to resolved, by module">
                <p className="text-3xl font-display font-semibold text-ink mb-3">
                  {data.resolutionTime.overall_avg_hours != null ? `${data.resolutionTime.overall_avg_hours}h` : "—"}
                  <span className="text-sm text-ink-faint font-body font-normal ml-2">overall</span>
                </p>
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={data.resolutionTime.by_module}>
                    <XAxis dataKey="module" tick={{ fontSize: 10 }} tickFormatter={(v) => v.replace("_", " ")} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="avg_hours" fill="#2F6F62" />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>

              <ChartCard title="Language distribution">
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie data={data.languageDist} dataKey="count" nameKey="label" outerRadius={80} label={(e) => e.label}>
                      {data.languageDist.map((entry, i) => (
                        <Cell key={entry.label} fill={CATEGORICAL_PALETTE[i % CATEGORICAL_PALETTE.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </ChartCard>
            </div>

            {/* Chart 8: Category distribution */}
            <ChartCard title="Complaint category distribution">
              <ResponsiveContainer width="100%" height={Math.max(200, data.categoryDist.length * 32)}>
                <BarChart data={data.categoryDist} layout="vertical" margin={{ left: 40 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1B2A4A20" />
                  <XAxis type="number" tick={{ fontSize: 11 }} allowDecimals={false} />
                  <YAxis type="category" dataKey="label" tick={{ fontSize: 11 }} width={160} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#E8A33D" />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            {/* Chart 10 + 11: AI classification / routing stats */}
            <div className="grid md:grid-cols-2 gap-4">
              <ChartCard title="AI classification statistics">
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <Stat label="Analyzed" value={data.aiClass.total_analyzed} />
                  <Stat label="Requires review" value={data.aiClass.requires_review_count} />
                  <Stat label="Avg module confidence" value={fmtPct(data.aiClass.avg_module_confidence)} />
                  <Stat label="Avg category confidence" value={fmtPct(data.aiClass.avg_category_confidence)} />
                  <Stat label="Admin overrides" value={data.aiClass.overridden_count} />
                  <Stat label="Override rate" value={`${data.aiClass.override_rate}%`} />
                </div>
              </ChartCard>
              <ChartCard title="AI routing statistics">
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <Stat label="Total routed" value={data.aiRouting.total_routed} />
                  <Stat label="Avg confidence" value={fmtPct(data.aiRouting.avg_confidence)} />
                  <Stat label="Admin overrides" value={data.aiRouting.overridden_count} />
                  <Stat label="Unrouted" value={data.aiRouting.unrouted_count} />
                </div>
              </ChartCard>
            </div>

            {/* Chart 13: Hotspots (simple table — full Leaflet map lives on the GIS-focused Complaints page) */}
            <ChartCard title="Geographic complaint hotspots" subtitle="Top grid cells by complaint count (~1.1km cells)">
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2">
                {data.hotspots.slice(0, 9).map((h, i) => (
                  <div key={i} className="border border-ink/10 p-3 text-sm flex items-center justify-between">
                    <div>
                      <p className="font-mono text-xs text-ink-faint">{h.latitude}, {h.longitude}</p>
                      <p className="text-ink-soft text-xs mt-0.5">{h.dominant_module.replace("_", " ")} · {h.dominant_priority}</p>
                    </div>
                    <span className="font-display text-lg font-semibold text-ink">{h.count}</span>
                  </div>
                ))}
              </div>
            </ChartCard>

            {/* Chart 14 + 15: Predictive */}
            <div className="grid md:grid-cols-2 gap-4">
              <ChartCard title="Predicted complaint volume" subtitle={data.predictedVolume.note}>
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={data.predictedVolume.points}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1B2A4A20" />
                    <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Line type="monotone" dataKey="predicted_count" stroke="#B23A2E" strokeDasharray="4 3" strokeWidth={2} dot />
                  </LineChart>
                </ResponsiveContainer>
                <p className="text-xs text-ink-faint mt-2">DEMO DATA — heuristic projection, not a trained model.</p>
              </ChartCard>

              <ChartCard title="Predicted high-risk areas" subtitle={data.predictedHotspots.note}>
                <div className="space-y-1.5 max-h-56 overflow-y-auto">
                  {data.predictedHotspots.areas.slice(0, 8).map((a, i) => (
                    <div key={i} className="flex items-center justify-between text-sm border-b border-dashed border-ink/10 pb-1.5">
                      <span className="font-mono text-xs text-ink-faint">{a.latitude}, {a.longitude}</span>
                      <span className="text-ink-soft">{a.module?.replace("_", " ")}</span>
                      <span className="font-semibold text-stamp-red">{Math.round(a.risk_score * 100)}% risk</span>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-ink-faint mt-2">DEMO DATA — frequency heuristic, not a trained spatial model.</p>
              </ChartCard>
            </div>
          </div>
        )}
      </div>
    </AdminLayout>
  );
}

function Stat({ label, value }) {
  return (
    <div>
      <p className="text-ink-faint text-xs">{label}</p>
      <p className="text-ink font-medium text-lg">{value ?? "—"}</p>
    </div>
  );
}

function fmtPct(v) {
  return v != null ? `${Math.round(v * 100)}%` : "—";
}
