/**
 * CareerLens Shared JSON Mock Contracts & State Fixtures
 * Matches the shared schema across microservices:
 * - auth-service (Node.js + Express, JWT)
 * - api (Python FastAPI)
 * - nlp service (OCR, NER, skills)
 * - scoring/ML service (LightGBM, scikit-learn, market)
 */

export const mockParsedResume = {
  resume_id: "res_skit_2026_091",
  name: "Aarav Sharma",
  email: "aarav.sharma@skit.ac.in",
  education: [
    {
      degree: "B.Tech in Computer Science & Engineering (Data Science)",
      institution: "Swami Keshvanand Institute of Technology (SKIT), Jaipur",
      year: "2023 - 2027"
    }
  ],
  experience: [
    {
      title: "Machine Learning Intern",
      company: "Cognitive AI Labs",
      start: "June 2025",
      end: "August 2025",
      bullets: [
        "Architected LightGBM inference microservices with FastAPI, cutting latency by 35% across 10,000+ daily candidate evaluations.",
        "Engineered Hugging Face Transformer NER extraction pipelines for OCR-scanned resume documents.",
        "Integrated ChromaDB vector search for automated semantic job-description matching."
      ]
    }
  ],
  skills: [
    { name: "Python", type: "explicit", confidence: 0.98, evidence: "Primary language for FastAPI, PyTorch and ML pipelines" },
    { name: "FastAPI", type: "explicit", confidence: 0.95, evidence: "Built asynchronous REST APIs verifying JWT tokens" },
    { name: "LightGBM", type: "explicit", confidence: 0.92, evidence: "Trained salary prediction and market fit tabular models" },
    { name: "Docker", type: "implicit", confidence: 0.86, evidence: "Containerized multi-service architectures with min 8GB RAM specs" },
    { name: "PostgreSQL", type: "explicit", confidence: 0.89, evidence: "Relational database schema for candidate profiles and scores" },
    { name: "ChromaDB", type: "explicit", confidence: 0.91, evidence: "Vector similarity index for semantic ATS scoring" }
  ],
  sections: {
    contact: true,
    summary: true,
    education: true,
    experience: true,
    skills: true,
    projects: true
  },
  raw_text: "Aarav Sharma | SKIT Jaipur | B.Tech CSE (Data Science) | Email: aarav.sharma@skit.ac.in | ML Intern at Cognitive AI Labs..."
};

export const mockScoreResult = {
  resume_id: "res_skit_2026_091",
  target_role: "Data Scientist / ML Engineer",
  ats_score: 82,
  breakdown: {
    keyword_match: 88,
    semantic_similarity: 84,
    section_completeness: 95,
    formatting: 90,
    experience_relevance: 78,
    quantified_impact: 72
  },
  skill_gap: {
    matched: ["Python", "FastAPI", "LightGBM", "Docker", "PostgreSQL", "ChromaDB"],
    missing: [
      { skill: "MLOps (MLflow / Kubeflow)", demand_pct: 88 },
      { skill: "Kubernetes Orchestration", demand_pct: 76 },
      { skill: "Distributed Training (Ray / PyTorch)", demand_pct: 65 }
    ],
    weak: [
      "Quantified Revenue Impact (Google XYZ format)",
      "Multi-Cloud Deployment (AWS/GCP)"
    ],
    trending: [
      "RAG Architecture & Embeddings",
      "LangChain / LlamaIndex",
      "Vector DB Retrieval Optimization"
    ]
  }
};

export const mockMarketFit = {
  resume_id: "res_skit_2026_091",
  fit_score: 78,
  salary_min: 8.5,
  salary_max: 14.2,
  currency: "INR",
  unit: "LPA",
  top_factors: [
    "High demand for FastAPI & LightGBM production skills in Indian Tier-1 tech hubs",
    "Tier-1 B.Tech Data Science foundational coursework matches emerging generative AI roles",
    "Projected upside: +3.5 LPA upon adding MLOps & Kubernetes container orchestration to verified skills"
  ]
};

export const mockRoadmap = {
  resume_id: "res_skit_2026_091",
  target_role: "Data Scientist / ML Engineer",
  phases: [
    {
      phase: "Phase 1: Production MLOps & Experiment Tracking",
      weeks: "Weeks 1-3",
      skills: ["MLflow", "Data Version Control (DVC)", "Model Registry"],
      resources: [
        {
          title: "Full Stack Deep Learning: Production MLOps",
          url: "https://fullstackdeeplearning.com",
          type: "Interactive Course"
        },
        {
          title: "MLflow Deployment Guide for Microservices",
          url: "https://mlflow.org/docs",
          type: "Documentation"
        }
      ],
      project: "Automated Model Packaging and Validation Pipeline with Git CI/CD",
      linked_gap_skill: "MLOps (MLflow / Kubeflow)"
    },
    {
      phase: "Phase 2: Cloud Containerization & Orchestration",
      weeks: "Weeks 4-6",
      skills: ["Kubernetes", "Helm", "Cloud Run / AWS EKS"],
      resources: [
        {
          title: "Kubernetes for Data Scientists & ML Engineers",
          url: "https://kubernetes.io/docs/tutorials",
          type: "Lab"
        }
      ],
      project: "Scalable ML Serving Cluster with Auto-Scaling and Health Probes",
      linked_gap_skill: "Kubernetes Orchestration"
    },
    {
      phase: "Phase 3: Production RAG Architectures & Vector Pipelines",
      weeks: "Weeks 7-9",
      skills: ["ChromaDB", "vLLM", "RAG Triad Evaluation"],
      resources: [
        {
          title: "ChromaDB Production Vector Index Optimization",
          url: "https://docs.trychroma.com",
          type: "Case Study"
        }
      ],
      project: "Enterprise RAG Assistant Grounded in Real-Time Market Job Feeds",
      linked_gap_skill: "RAG Architecture & Embeddings"
    }
  ]
};

export const mockCritique = {
  resume_id: "res_skit_2026_091",
  agents: [
    {
      persona: "Recruiter",
      score: 85,
      verdict: "Strong candidate profile; effortlessly passes the standard 6-second recruiter glance.",
      strengths: [
        "Target role keywords (Data Scientist, ML Engineer) are immediately visible in the header.",
        "Clear institutional pedigree (SKIT Jaipur, CSE Data Science) aligns with campus hiring criteria."
      ],
      concerns: [
        "Professional summary contains generic phrases ('results-driven', 'hardworking').",
        "Graduation date should explicitly mention 'Expected June 2027'."
      ],
      rewrites: [
        {
          before: "Worked on machine learning models and helped improve performance for the team.",
          after: "Engineered LightGBM inference microservices with FastAPI, cutting latency by 35% across 10,000+ daily candidate evaluations."
        }
      ]
    },
    {
      persona: "HR",
      score: 80,
      verdict: "High academic alignment with SDG 4 (Quality Education) competencies and strong work ethic.",
      strengths: [
        "Consistent timeline with clear continuity in technical projects.",
        "Demonstrated peer leadership during the ML internship."
      ],
      concerns: [
        "Add more explicit examples of cross-functional collaboration and stakeholder presentations."
      ],
      rewrites: [
        {
          before: "Helped team members learn new machine learning libraries.",
          after: "Conducted 4 technical workshops on Git workflows and FastAPI best practices, accelerating team onboarding ramp-up by 2 weeks."
        }
      ]
    },
    {
      persona: "Hiring Manager",
      score: 81,
      verdict: "Technically solid with modern stack choices; requires concrete production resilience proof.",
      strengths: [
        "Direct production usage of vector databases (ChromaDB) and Hugging Face NER.",
        "Distinguishes between explicit and implicit skill classifications."
      ],
      concerns: [
        "No mention of automated unit testing (pytest) or CI/CD test coverage in bullet points.",
        "Lacks memory footprint and concurrency benchmarks for the FastAPI microservice."
      ],
      rewrites: [
        {
          before: "Built FastAPI backend to serve model predictions.",
          after: "Architected asynchronous FastAPI inference service handling 120 req/sec at <45ms p99 latency with automated PyTest coverage exceeding 90%."
        }
      ]
    }
  ],
  merged: {
    verdict: "Recommended for Technical Screening. Exceptional core algorithmic grounding with high growth potential.",
    consensus_score: 82,
    agreements: [
      "High proficiency in modern Python ML stack (FastAPI, LightGBM, Vector DBs).",
      "Bullet points must adopt the Google XYZ format (Accomplished [X] measured by [Y] by doing [Z])."
    ],
    disagreements: [
      "Recruiter preferred concise 1-line bullets; Hiring Manager requested deeper architectural parameters."
    ]
  }
};

export const mockApiError = {
  error: {
    code: "UPSTREAM_MARKET_FEED_TIMEOUT",
    message: "Live LinkedIn/job-board API exceeded latency threshold (5000ms). Falling back to cached ChromaDB market demand index."
  }
};
