"use client";

import { useState, useEffect, useCallback } from "react";
import { fetchDashboard, fetchSeries, fetchHealth } from "@/lib/api";
import { DashboardResponse, SeriesResponse, HealthResponse } from "@/types/series";

export function useMarketData(refreshInterval = 60000) {
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [selectedSeries, setSelectedSeries] = useState<SeriesResponse | null>(null);
  const [selectedId, setSelectedId] = useState("usd_clp");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboard = useCallback(async () => {
    try {
      const [dashData, healthData] = await Promise.all([
        fetchDashboard(),
        fetchHealth(),
      ]);
      setDashboard(dashData);
      setHealth(healthData);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error de conexion");
    }
  }, []);

  const loadSeries = useCallback(async (panelId: string) => {
    try {
      // Cargar últimos 2 años para el gráfico
      const now = new Date();
      const twoYearsAgo = new Date(now);
      twoYearsAgo.setFullYear(now.getFullYear() - 2);
      const from = twoYearsAgo.toISOString().split("T")[0];
      const to = now.toISOString().split("T")[0];

      const seriesData = await fetchSeries(panelId, from, to);
      setSelectedSeries(seriesData);
    } catch (e) {
      console.error("Error loading series:", e);
    }
  }, []);

  // Cargar dashboard inicial
  useEffect(() => {
    setLoading(true);
    loadDashboard().finally(() => setLoading(false));
  }, [loadDashboard]);

  // Auto-refresh del dashboard
  useEffect(() => {
    const interval = setInterval(loadDashboard, refreshInterval);
    return () => clearInterval(interval);
  }, [loadDashboard, refreshInterval]);

  // Cargar serie seleccionada
  useEffect(() => {
    loadSeries(selectedId);
  }, [selectedId, loadSeries]);

  const selectSeries = useCallback((id: string) => {
    setSelectedId(id);
  }, []);

  return {
    dashboard,
    health,
    selectedSeries,
    selectedId,
    selectSeries,
    loading,
    error,
    refresh: loadDashboard,
  };
}
