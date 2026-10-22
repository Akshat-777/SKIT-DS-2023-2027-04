/**
 * CareerLens ATS Score & Skill Gap Mock JSON Fixtures
 * Adheres strictly to the ScoreResult contract:
 * {
 *   ats_score: number,
 *   target_role: string,
 *   breakdown: {
 *     keyword_match: number,
 *     semantic_similarity: number,
 *     section_completeness: number,
 *     formatting: number,
 *     experience_relevance: number,
 *     quantified_impact: number
 *   },
 *   skill_gap: {
 *     matched: string[],
 *     missing: Array<{ skill: string, demand_pct: number, category?: string, why_matters?: string, ats_boost?: string, action_tip?: string, sample_bullet?: string }>,
 *     weak: string[],
 *     trending: string[]
 *   }
 * }
 */

export const mockSkillDetails = {
  "MLOps (MLflow / Kubeflow)": {
    skill: "MLOps (MLflow / Kubeflow)",
    demand_pct: 88,
    category: "ML Infrastructure",
    why_matters: "Production AI systems require lifecycle management. Over 88% of Senior ML Engineer job descriptions now prioritize candidates with end-to-end model registry, tracking, and automated retraining pipelines over raw Jupyter notebook prototyping.",
    ats_boost: "+28% ATS Pass Rate",
    action_tip: "Build a complete MLflow tracking experiment and Kubeflow pipeline deploying a sentiment or classification model with automated drift monitoring.",
    sample_bullet: "Architected end-to-end MLflow model registry and Kubeflow CI/CD pipelines, automating model retraining and reducing deployment latency by 45% across 4 production microservices."
  },
  "Kubernetes Orchestration": {
    skill: "Kubernetes Orchestration",
    demand_pct: 76,
    category: "Cloud & Distributed Systems",
    why_matters: "Enterprises host microservices and model serving clusters on K8s. Missing container orchestration keywords flags candidate resumes as junior or research-only in recruiter screening algorithms.",
    ats_boost: "+22% ATS Pass Rate",
    action_tip: "Containerize your API and ML inference services with Docker, create multi-node Helm charts, and configure Horizontal Pod Autoscaling (HPA).",
    sample_bullet: "Deployed and orchestrated 6 FastAPI microservices via Kubernetes Helm charts with automated HPA, sustaining 10,000+ daily RPM at 99.98% uptime."
  },
  "Distributed Training (Ray / PyTorch)": {
    skill: "Distributed Training (Ray / PyTorch)",
    demand_pct: 65,
    category: "High-Performance Computing",
    why_matters: "Large language models and heavy transformer fine-tuning exceed single-GPU memory. Tech recruiters look for distributed compute frameworks like Ray, PyTorch DDP, or DeepSpeed.",
    ats_boost: "+18% ATS Pass Rate",
    action_tip: "Fine-tune an open-source model using PyTorch DistributedDataParallel (DDP) or Ray Train across multiple virtual GPU workers.",
    sample_bullet: "Optimized Transformer model fine-tuning with PyTorch DDP and Ray Train across multi-GPU nodes, accelerating training convergence time by 60%."
  },
  "RAG Architecture & Embeddings": {
    skill: "RAG Architecture & Embeddings",
    demand_pct: 92,
    category: "Generative AI",
    why_matters: "Retrieval-Augmented Generation is the #1 most cited architecture requirement in 2026 AI job postings. Resumes featuring vector databases and semantic reranking receive top algorithmic ranking.",
    ats_boost: "+35% ATS Pass Rate",
    action_tip: "Implement hybrid dense-sparse retrieval using ChromaDB and reciprocal rank fusion for document question-answering systems.",
    sample_bullet: "Engineered production RAG search architecture with ChromaDB vector embeddings and cross-encoder reranking, raising answer accuracy from 72% to 94% on domain corpus."
  },
  "LangChain / LlamaIndex": {
    skill: "LangChain / LlamaIndex",
    demand_pct: 85,
    category: "LLM Tooling",
    why_matters: "Industry standard frameworks for chaining prompts, tool calling, and structured output parsing. Recruiters search specifically for these exact keyword tokens.",
    ats_boost: "+24% ATS Pass Rate",
    action_tip: "Build an autonomous agent with LlamaIndex query engines or LangGraph stateful multi-agent workflows.",
    sample_bullet: "Developed multi-agent decision workflows using LangChain and FastAPI, cutting document triage processing time by 70%."
  },
  "Vector DB Retrieval Optimization": {
    skill: "Vector DB Retrieval Optimization",
    demand_pct: 82,
    category: "Data Engineering",
    why_matters: "Scaling vector similarity beyond 100K vectors requires HNSW indexing, quantization, and cosine distance pruning.",
    ats_boost: "+20% ATS Pass Rate",
    action_tip: "Benchmark HNSW vs IVF indexing in Milvus, Pinecone, or ChromaDB under concurrent query load.",
    sample_bullet: "Tuned ChromaDB HNSW vector index parameters and vector quantization, cutting p99 semantic search latency from 240ms to 38ms."
  },
  "Quantified Revenue Impact (Google XYZ format)": {
    skill: "Quantified Revenue Impact (Google XYZ format)",
    demand_pct: 95,
    category: "Recruiter Criteria",
    why_matters: "ATS semantic parsers look for metric symbols (%, $, hours, ms) preceding action verbs. Bullet points lacking quantifiable impact score in the lowest 25th percentile of recruiter fit.",
    ats_boost: "+32% ATS Pass Rate",
    action_tip: "Rewrite every past job bullet to follow: 'Accomplished [X] as measured by [Y] by doing [Z]'.",
    sample_bullet: "Cut cloud infrastructure expenditure by $14,000/month by optimizing LightGBM inference batching and downscaling idle nodes."
  },
  "Multi-Cloud Deployment (AWS/GCP)": {
    skill: "Multi-Cloud Deployment (AWS/GCP)",
    demand_pct: 80,
    category: "DevOps & Cloud",
    why_matters: "Cloud agnosticism and Terraform infrastructure-as-code prevent vendor lock-in. Essential for enterprise roles.",
    ats_boost: "+21% ATS Pass Rate",
    action_tip: "Provision AWS ECS / GCP Cloud Run microservices using modular Terraform configurations.",
    sample_bullet: "Authored Terraform HCL modules provisioning serverless microservices on AWS and GCP with automated secrets rotation."
  },
  "Python": {
    skill: "Python",
    demand_pct: 96,
    category: "Core Languages",
    why_matters: "Primary lingua franca for machine learning, data engineering, and modern web APIs. Strongly verified in your resume.",
    ats_boost: "Verified Pass",
    action_tip: "Maintain proficiency and highlight async/await concurrency and typing annotations.",
    sample_bullet: "Engineered high-throughput asynchronous Python 3.12 pipelines processing 1M+ daily records."
  },
  "FastAPI": {
    skill: "FastAPI",
    demand_pct: 89,
    category: "Web Frameworks",
    why_matters: "High-performance ASGI framework widely favored for ML model serving and REST APIs. Verified in your resume.",
    ats_boost: "Verified Pass",
    action_tip: "Highlight Pydantic v2 validation, OpenAPI documentation, and dependency injection.",
    sample_bullet: "Developed asynchronous REST API endpoints with FastAPI and Pydantic v2, serving 500 RPS."
  },
  "LightGBM": {
    skill: "LightGBM",
    demand_pct: 78,
    category: "Machine Learning",
    why_matters: "Industry standard gradient boosting framework for tabular and structured business data. Verified in your resume.",
    ats_boost: "Verified Pass",
    action_tip: "Highlight hyperparameter tuning (Optuna) and SHAP explainability.",
    sample_bullet: "Trained LightGBM tabular models achieving 0.91 AUC with SHAP feature importance analysis."
  },
  "Docker": {
    skill: "Docker",
    demand_pct: 87,
    category: "Containerization",
    why_matters: "Essential containerization baseline for reproducible software deployments.",
    ats_boost: "Verified Pass",
    action_tip: "Emphasize multi-stage builds and minimal Alpine/distroless base images.",
    sample_bullet: "Containerized microservices using Docker multi-stage builds, shrinking image footprint by 65%."
  },
  "PostgreSQL": {
    skill: "PostgreSQL",
    demand_pct: 84,
    category: "Databases",
    why_matters: "Most popular enterprise open-source relational database with pgvector extensions.",
    ats_boost: "Verified Pass",
    action_tip: "Highlight indexed query optimization, transactions, and migration management.",
    sample_bullet: "Designed PostgreSQL normalized schema and query indexes, reducing join latency by 40%."
  },
  "ChromaDB": {
    skill: "ChromaDB",
    demand_pct: 79,
    category: "Vector Databases",
    why_matters: "Fast, developer-friendly vector store for embedding similarity search and semantic indexing.",
    ats_boost: "Verified Pass",
    action_tip: "Showcase persistent collections and cosine similarity ranking pipelines.",
    sample_bullet: "Integrated ChromaDB vector store powering real-time semantic resume-to-job matching."
  }
};

/**
 * Standard Score Result: Good (82)
 */
export const mockScoreGood = {
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

/**
 * Poor Score Fixture: 42 (Critical Gaps)
 */
export const mockScorePoor = {
  resume_id: "res_poor_candidate_001",
  target_role: "Data Scientist / ML Engineer",
  ats_score: 42,
  breakdown: {
    keyword_match: 38,
    semantic_similarity: 45,
    section_completeness: 55,
    formatting: 48,
    experience_relevance: 40,
    quantified_impact: 28
  },
  skill_gap: {
    matched: ["Python", "Docker"],
    missing: [
      { skill: "MLOps (MLflow / Kubeflow)", demand_pct: 88 },
      { skill: "Kubernetes Orchestration", demand_pct: 76 },
      { skill: "FastAPI", demand_pct: 89 },
      { skill: "PostgreSQL", demand_pct: 84 },
      { skill: "Distributed Training (Ray / PyTorch)", demand_pct: 65 }
    ],
    weak: [
      "Quantified Revenue Impact (Google XYZ format)",
      "Non-standard resume headings detected",
      "Missing production metrics and outcomes"
    ],
    trending: [
      "RAG Architecture & Embeddings",
      "LangChain / LlamaIndex"
    ]
  }
};

/**
 * Fair Score Fixture: 64 (Moderate Fit)
 */
export const mockScoreFair = {
  resume_id: "res_fair_candidate_002",
  target_role: "Data Scientist / ML Engineer",
  ats_score: 64,
  breakdown: {
    keyword_match: 68,
    semantic_similarity: 62,
    section_completeness: 80,
    formatting: 75,
    experience_relevance: 58,
    quantified_impact: 52
  },
  skill_gap: {
    matched: ["Python", "Docker", "PostgreSQL", "FastAPI"],
    missing: [
      { skill: "MLOps (MLflow / Kubeflow)", demand_pct: 88 },
      { skill: "Distributed Training (Ray / PyTorch)", demand_pct: 65 },
      { skill: "ChromaDB", demand_pct: 79 }
    ],
    weak: [
      "Quantified Revenue Impact (Google XYZ format)",
      "Multi-Cloud Deployment (AWS/GCP)"
    ],
    trending: [
      "RAG Architecture & Embeddings",
      "Vector DB Retrieval Optimization"
    ]
  }
};

/**
 * Excellent Score Fixture: 94 (Recruiter-Ready)
 */
export const mockScoreExcellent = {
  resume_id: "res_excellent_candidate_003",
  target_role: "Data Scientist / ML Engineer",
  ats_score: 94,
  breakdown: {
    keyword_match: 96,
    semantic_similarity: 92,
    section_completeness: 98,
    formatting: 95,
    experience_relevance: 92,
    quantified_impact: 90
  },
  skill_gap: {
    matched: ["Python", "FastAPI", "LightGBM", "Docker", "PostgreSQL", "ChromaDB", "Kubernetes Orchestration"],
    missing: [
      { skill: "MLOps (MLflow / Kubeflow)", demand_pct: 88 }
    ],
    weak: [
      "Multi-Cloud Deployment (AWS/GCP)"
    ],
    trending: [
      "RAG Architecture & Embeddings",
      "LangChain / LlamaIndex",
      "Vector DB Retrieval Optimization"
    ]
  }
};

/**
 * Empty Gaps Fixture: 100% Core Competencies Matched
 */
export const mockScoreNoGaps = {
  resume_id: "res_perfect_candidate_004",
  target_role: "Data Scientist / ML Engineer",
  ats_score: 98,
  breakdown: {
    keyword_match: 98,
    semantic_similarity: 97,
    section_completeness: 100,
    formatting: 96,
    experience_relevance: 98,
    quantified_impact: 97
  },
  skill_gap: {
    matched: [
      "Python",
      "FastAPI",
      "LightGBM",
      "Docker",
      "PostgreSQL",
      "ChromaDB",
      "Kubernetes Orchestration",
      "MLOps (MLflow / Kubeflow)",
      "Distributed Training (Ray / PyTorch)"
    ],
    missing: [],
    weak: [],
    trending: [
      "RAG Architecture & Embeddings",
      "LangChain / LlamaIndex"
    ]
  }
};

/**
 * Target Roles Fixture Database
 */
export const mockRoleFixtures = {
  "Data Scientist / ML Engineer": mockScoreGood,
  "Full Stack AI Engineer": {
    resume_id: "res_fs_ai_2026",
    target_role: "Full Stack AI Engineer",
    ats_score: 74,
    breakdown: {
      keyword_match: 76,
      semantic_similarity: 78,
      section_completeness: 90,
      formatting: 88,
      experience_relevance: 70,
      quantified_impact: 66
    },
    skill_gap: {
      matched: ["Python", "FastAPI", "Docker", "PostgreSQL"],
      missing: [
        { skill: "React / Next.js State Hydration", demand_pct: 91 },
        { skill: "Tailwind CSS Design Tokens", demand_pct: 82 },
        { skill: "WebSocket Streaming AI Responses", demand_pct: 79 }
      ],
      weak: [
        "End-to-End Cypress / Playwright E2E Testing",
        "SSR Bundle Optimization"
      ],
      trending: [
        "Vercel AI SDK Integration",
        "Local Small Language Models (Ollama)",
        "Server Actions with Zod"
      ]
    }
  },
  "DevOps & Cloud Architect": {
    resume_id: "res_devops_2026",
    target_role: "DevOps & Cloud Architect",
    ats_score: 59,
    breakdown: {
      keyword_match: 55,
      semantic_similarity: 60,
      section_completeness: 85,
      formatting: 82,
      experience_relevance: 52,
      quantified_impact: 58
    },
    skill_gap: {
      matched: ["Docker", "PostgreSQL"],
      missing: [
        { skill: "Terraform Infrastructure as Code", demand_pct: 94 },
        { skill: "Kubernetes Orchestration", demand_pct: 89 },
        { skill: "Prometheus & Grafana Observability", demand_pct: 81 }
      ],
      weak: [
        "Zero-Trust Cloud IAM Policies",
        "CI/CD GitOps with ArgoCD"
      ],
      trending: [
        "eBPF Kernel Network Observability",
        "FinOps Cloud Cost Automation",
        "OpenTelemetry Unified Traces"
      ]
    }
  },
  "Data Platform Engineer": {
    resume_id: "res_data_eng_2026",
    target_role: "Data Platform Engineer",
    ats_score: 86,
    breakdown: {
      keyword_match: 90,
      semantic_similarity: 86,
      section_completeness: 95,
      formatting: 92,
      experience_relevance: 84,
      quantified_impact: 78
    },
    skill_gap: {
      matched: ["Python", "Docker", "PostgreSQL", "FastAPI", "ChromaDB"],
      missing: [
        { skill: "Apache Spark / Databricks Delta Lake", demand_pct: 89 },
        { skill: "Kafka Real-Time Streaming", demand_pct: 82 }
      ],
      weak: [
        "dbt Semantic Data Modeling",
        "Iceberg Partitioning Optimization"
      ],
      trending: [
        "DuckDB In-Memory OLAP",
        "Apache Arrow Columnar Transport",
        "Polars Accelerated DataFrames"
      ]
    }
  }
};
