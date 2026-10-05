/**
 * CareerLens Dashboard & Analytics Service
 * Connects to Python FastAPI ML/Scoring & LLM Multi-Agent Critique Service
 *
 * Implements Shared Contracts:
 * - ScoreResult: ATS Score + Skill Gap vs live job-market demand
 * - MarketFit: LightGBM Salary Range (INR LPA) + Market Fit Score
 * - Roadmap: RAG-Grounded Curated Learning Phases & Projects
 * - Critique: Multi-Agent Recruiter Persona (Recruiter, HR, Hiring Manager)
 */

import { apiClient, IS_MOCK_MODE } from './apiClient';
import { mockScoreResult, mockMarketFit, mockRoadmap, mockCritique } from '../data/mockData';

const MOCK_DELAY = 300;

export const dashboardService = {
  /**
   * Fetch ATS Score and Real-time Skill Gap Analysis
   * @param {string} resumeId
   * @param {string} targetRole
   * @returns {Promise<typeof mockScoreResult>}
   */
  async getAtsScore(resumeId, targetRole = 'Data Scientist') {
    if (IS_MOCK_MODE || resumeId.startsWith('mock-')) {
      await new Promise((r) => setTimeout(r, MOCK_DELAY));
      return {
        ...mockScoreResult,
        resume_id: resumeId,
        target_role: targetRole || mockScoreResult.target_role,
      };
    }

    try {
      const data = await apiClient.get(`/analysis/${resumeId}/ats-score`, {
        params: { target_role: targetRole },
      });
      return data;
    } catch (err) {
      console.warn(`dashboardService.getAtsScore fallback for ${resumeId}:`, err.message);
      return {
        ...mockScoreResult,
        resume_id: resumeId,
        target_role: targetRole || mockScoreResult.target_role,
      };
    }
  },

  /**
   * Fetch LightGBM Market Fit Score and Salary Range Prediction
   * @param {string} resumeId
   * @returns {Promise<typeof mockMarketFit>}
   */
  async getMarketFit(resumeId) {
    if (IS_MOCK_MODE || resumeId.startsWith('mock-')) {
      await new Promise((r) => setTimeout(r, MOCK_DELAY));
      return {
        ...mockMarketFit,
        resume_id: resumeId,
      };
    }

    try {
      const data = await apiClient.get(`/analysis/${resumeId}/market-fit`);
      return data;
    } catch (err) {
      console.warn(`dashboardService.getMarketFit fallback for ${resumeId}:`, err.message);
      return {
        ...mockMarketFit,
        resume_id: resumeId,
      };
    }
  },

  /**
   * Fetch RAG-Grounded Personalized Learning Roadmap
   * @param {string} resumeId
   * @param {string} targetRole
   * @returns {Promise<typeof mockRoadmap>}
   */
  async getRoadmap(resumeId, targetRole) {
    if (IS_MOCK_MODE || resumeId.startsWith('mock-')) {
      await new Promise((r) => setTimeout(r, MOCK_DELAY));
      return {
        ...mockRoadmap,
        resume_id: resumeId,
        target_role: targetRole || mockRoadmap.target_role,
      };
    }

    try {
      const data = await apiClient.get(`/analysis/${resumeId}/roadmap`, {
        params: { target_role: targetRole },
      });
      return data;
    } catch (err) {
      console.warn(`dashboardService.getRoadmap fallback for ${resumeId}:`, err.message);
      return {
        ...mockRoadmap,
        resume_id: resumeId,
        target_role: targetRole || mockRoadmap.target_role,
      };
    }
  },

  /**
   * Fetch Multi-Agent Recruiter Persona Critique Report
   * @param {string} resumeId
   * @returns {Promise<typeof mockCritique>}
   */
  async getCritique(resumeId) {
    if (IS_MOCK_MODE || resumeId.startsWith('mock-')) {
      await new Promise((r) => setTimeout(r, MOCK_DELAY));
      return {
        ...mockCritique,
        resume_id: resumeId,
      };
    }

    try {
      const data = await apiClient.get(`/analysis/${resumeId}/critique`);
      return data;
    } catch (err) {
      console.warn(`dashboardService.getCritique fallback for ${resumeId}:`, err.message);
      return {
        ...mockCritique,
        resume_id: resumeId,
      };
    }
  },
};

export default dashboardService;
