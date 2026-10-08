/**
 * CareerLens Dashboard & Analytics Service
 * Connects to Python FastAPI ML/Scoring & LLM Multi-Agent Critique Service
 *
 * Implements Shared Contracts:
 * - ScoreResult: ATS Score + Skill Gap vs live job-market demand
 * - MarketFit: LightGBM Salary Range (INR LPA) + Market Fit Score
 * - Roadmap: RAG-Grounded Curated Learning Phases & Projects
 * - Critique: Multi-Agent Recruiter Persona (Recruiter, HR, Hiring Manager)
 *
 * Mock mode: only triggered when resumeId starts with 'mock-'
 * Real mode: all other resumeIds go directly to the FastAPI backend
 */

import { apiClient } from './apiClient';
import { mockScoreResult, mockMarketFit, mockRoadmap, mockCritique } from '../data/mockData';

const MOCK_DELAY = 300;
const isMockId = (resumeId) => resumeId?.startsWith('mock-');

export const dashboardService = {
  /**
   * Fetch ATS Score and Real-time Skill Gap Analysis
   * @param {string} resumeId
   * @param {string} targetRole
   * @returns {Promise<typeof mockScoreResult>}
   */
  async getAtsScore(resumeId, targetRole = 'Data Scientist') {
    if (isMockId(resumeId)) {
      await new Promise((r) => setTimeout(r, MOCK_DELAY));
      return { ...mockScoreResult, resume_id: resumeId, target_role: targetRole || mockScoreResult.target_role };
    }

    const data = await apiClient.get(`/resumes/${resumeId}/analysis`);
    // Backend returns { parsed_resume, score_result }
    return data?.score_result ?? data;
  },

  /**
   * Fetch LightGBM Market Fit Score and Salary Range Prediction
   * @param {string} resumeId
   * @returns {Promise<typeof mockMarketFit>}
   */
  async getMarketFit(resumeId) {
    if (isMockId(resumeId)) {
      await new Promise((r) => setTimeout(r, MOCK_DELAY));
      return { ...mockMarketFit, resume_id: resumeId };
    }

    return apiClient.get(`/resumes/${resumeId}/market-fit`);
  },

  /**
   * Fetch RAG-Grounded Personalised Learning Roadmap
   * @param {string} resumeId
   * @param {string} targetRole
   * @returns {Promise<typeof mockRoadmap>}
   */
  async getRoadmap(resumeId, targetRole) {
    if (isMockId(resumeId)) {
      await new Promise((r) => setTimeout(r, MOCK_DELAY));
      return { ...mockRoadmap, resume_id: resumeId, target_role: targetRole || mockRoadmap.target_role };
    }

    return apiClient.get(`/resumes/${resumeId}/roadmap`, {
      params: { target_role: targetRole },
    });
  },

  /**
   * Fetch Multi-Agent Recruiter Persona Critique Report
   * @param {string} resumeId
   * @returns {Promise<typeof mockCritique>}
   */
  async getCritique(resumeId) {
    if (isMockId(resumeId)) {
      await new Promise((r) => setTimeout(r, MOCK_DELAY));
      return { ...mockCritique, resume_id: resumeId };
    }

    return apiClient.get(`/resumes/${resumeId}/critique`);
  },
};

export default dashboardService;
