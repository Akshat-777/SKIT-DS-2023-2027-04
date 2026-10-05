/**
 * CareerLens useDashboard Hook
 * Loads analytics, ATS score breakdown, LightGBM market-fit, RAG roadmap, and critique reports.
 */

import { useState, useCallback } from 'react';
import { dashboardService } from '../services/dashboardService';

export function useDashboard() {
  const [atsScore, setAtsScore] = useState(null);
  const [marketFit, setMarketFit] = useState(null);
  const [roadmap, setRoadmap] = useState(null);
  const [critique, setCritique] = useState(null);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Fetch all dashboard data for a given resume
   */
  const loadAllAnalytics = useCallback(async (resumeId, targetRole) => {
    setIsLoading(true);
    setError(null);

    try {
      const [scoreRes, marketRes, roadRes, critRes] = await Promise.all([
        dashboardService.getAtsScore(resumeId, targetRole),
        dashboardService.getMarketFit(resumeId),
        dashboardService.getRoadmap(resumeId, targetRole),
        dashboardService.getCritique(resumeId),
      ]);

      setAtsScore(scoreRes);
      setMarketFit(marketRes);
      setRoadmap(roadRes);
      setCritique(critRes);

      return { scoreRes, marketRes, roadRes, critRes };
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadAtsScore = useCallback(async (resumeId, targetRole) => {
    setIsLoading(true);
    try {
      const data = await dashboardService.getAtsScore(resumeId, targetRole);
      setAtsScore(data);
      return data;
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadMarketFit = useCallback(async (resumeId) => {
    setIsLoading(true);
    try {
      const data = await dashboardService.getMarketFit(resumeId);
      setMarketFit(data);
      return data;
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadRoadmap = useCallback(async (resumeId, targetRole) => {
    setIsLoading(true);
    try {
      const data = await dashboardService.getRoadmap(resumeId, targetRole);
      setRoadmap(data);
      return data;
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadCritique = useCallback(async (resumeId) => {
    setIsLoading(true);
    try {
      const data = await dashboardService.getCritique(resumeId);
      setCritique(data);
      return data;
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    atsScore,
    marketFit,
    roadmap,
    critique,
    isLoading,
    error,
    loadAllAnalytics,
    loadAtsScore,
    loadMarketFit,
    loadRoadmap,
    loadCritique,
  };
}

export default useDashboard;
