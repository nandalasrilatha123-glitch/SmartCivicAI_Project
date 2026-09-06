import api from "./api";

const get = (path, params) => api.get(path, { params }).then((r) => r.data);

export const getOverview = (params) => get("/analytics/overview", params);
export const getStatusDistribution = (params) => get("/analytics/status-distribution", params);
export const getByModule = (params) => get("/analytics/by-module", params);
export const getOverTime = (params) => get("/analytics/over-time", params);
export const getModuleStatusMatrix = (params) => get("/analytics/module-status-matrix", params);
export const getPriorityDistribution = (params) => get("/analytics/priority-distribution", params);
export const getDepartmentPerformance = (params) => get("/analytics/department-performance", params);
export const getResolutionTime = (params) => get("/analytics/resolution-time", params);
export const getCategoryDistribution = (params) => get("/analytics/category-distribution", params);
export const getLanguageDistribution = (params) => get("/analytics/language-distribution", params);
export const getAIClassificationStats = () => get("/analytics/ai-classification-stats");
export const getAIRoutingStats = () => get("/analytics/ai-routing-stats");
export const getMyDepartmentOverview = () => get("/analytics/my-department");
export const getHotspots = (params) => get("/analytics/hotspots", params);
export const getPredictedVolume = (params) => get("/analytics/predicted-volume", params);
export const getPredictedHotspots = (params) => get("/analytics/predicted-hotspots", params);
