"""Evaluation Module for CareerLens Two-Layer Skill Extraction.
Contains a labeled dataset of 20 diverse resumes across disciplines,
calculates Precision, Recall, and F1 for explicit and implicit extraction layers,
and generates a threshold tuning analysis table.
"""

from __future__ import annotations

import os
import sys

# Ensure backend root is on sys.path
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

import logging
from typing import Any, Dict, List, Set, Tuple

from careerlens.nlp.skill_extractor import TwoLayerSkillExtractor

LOG = logging.getLogger("careerlens.nlp.evaluation")

# ==================== 20 LABELED BENCHMARK RESUMES ====================
LABELED_RESUMES: List[Dict[str, Any]] = [
    {
        "id": "res_01",
        "domain": "Full-Stack Web Developer",
        "text": """
Aishani Billore - Full Stack Developer
Email: aishani@example.com

[EDUCATION]
B.Tech Computer Science, SKIT Jaipur (2024)

[EXPERIENCE]
Software Engineer Intern at WebSolutions (2023 - 2024)
- Architected RESTful API endpoints and integrated PostgreSQL with async connection pooling.
- Built reusable single-page application UI components with dynamic state management.
- Containerized frontend and backend services for deployment.

[SKILLS]
React, Node.js, PostgreSQL, Docker, Git, JavaScript
""",
        "ground_truth_explicit": {"React", "Node.js", "PostgreSQL", "Docker", "Git", "JavaScript"},
        "ground_truth_implicit": {"REST API", "Backend Development", "Frontend Development"}
    },
    {
        "id": "res_02",
        "domain": "Backend & Distributed Systems",
        "text": """
Akshat Agarwal - Backend Engineer
Email: akshat@example.com

[EXPERIENCE]
Senior Backend Engineer at CloudScale (2022 - Present)
- Developed high-throughput microservices handling 25,000 requests per second.
- Deployed container clusters on Amazon EKS and automated multi-stage CI/CD pipelines.
- Distributed incoming HTTP traffic using round-robin reverse proxies.

[SKILLS]
Go, Kubernetes, Redis, Microservices, CI/CD, AWS
""",
        "ground_truth_explicit": {"Go", "Kubernetes", "Redis", "Microservices", "CI/CD", "AWS"},
        "ground_truth_implicit": {"Distributed Systems", "Load Balancing", "Backend Development"}
    },
    {
        "id": "res_03",
        "domain": "Machine Learning Engineer",
        "text": """
Aryan Rathore - Machine Learning Engineer
Email: aryan@example.com

[EXPERIENCE]
Machine Learning Engineer at DataMinds (2022 - 2024)
- Fine-tuned transformer models for token classification and entity recognition.
- Selected predictive features and tuned hyperparameters to prevent model overfitting.
- Tracked experiment loss curves, metrics, and registered production models.

[SKILLS]
Python, PyTorch, Transformers, Scikit-learn, MLflow, Machine Learning
""",
        "ground_truth_explicit": {"Python", "PyTorch", "Hugging Face Transformers", "Scikit-learn", "MLflow", "Machine Learning"},
        "ground_truth_implicit": {"Natural Language Processing", "Feature Engineering", "Hyperparameter Tuning"}
    },
    {
        "id": "res_04",
        "domain": "DevOps & Cloud Engineer",
        "text": """
Rohan Sharma - DevOps Engineer
Email: rohan@example.com

[EXPERIENCE]
Cloud Infrastructure Engineer at InfraOps (2021 - 2023)
- Provisioned reproducible cloud infrastructure using declarative HCL modules.
- Packaged microservice deployment manifests and values into versioned charts.
- Configured real-time system monitoring dashboards and metric alerts.

[SKILLS]
Terraform, Docker, Kubernetes, Helm, Linux, AWS
""",
        "ground_truth_explicit": {"Terraform", "Docker", "Kubernetes", "Helm", "Linux", "AWS"},
        "ground_truth_implicit": {"Infrastructure as Code", "Site Reliability Engineering"}
    },
    {
        "id": "res_05",
        "domain": "Data Engineer",
        "text": """
Priya Verma - Data Engineer
Email: priya@example.com

[EXPERIENCE]
Data Pipeline Engineer at BigData Corp (2021 - 2024)
- Engineered distributed batch transformation pipelines processing terabytes of clickstream logs.
- Orchestrated daily scheduled ETL workflows with dependency DAGs and retry alerts.
- Partitioned relational analytical warehouses using star schemas.

[SKILLS]
Apache Spark, PySpark, Apache Airflow, SQL, Python, PostgreSQL
""",
        "ground_truth_explicit": {"Apache Spark", "PySpark", "Apache Airflow", "SQL", "Python", "PostgreSQL"},
        "ground_truth_implicit": {"ETL Pipelines", "Data Warehousing", "Data Modeling"}
    },
    {
        "id": "res_06",
        "domain": "Mobile App Developer (Android)",
        "text": """
Vikram Meena - Android Engineer
Email: vikram@example.com

[EXPERIENCE]
Mobile Developer at AppWorks (2022 - Present)
- Engineered native mobile client interfaces using declarative composable UI components.
- Stored local application entities with SQLite DAOs and reactive observation streams.
- Published release builds to app stores with automated crash monitoring.

[SKILLS]
Kotlin, Android Development, Jetpack Compose, SQLite, Git
""",
        "ground_truth_explicit": {"Kotlin", "Android Development", "Jetpack Compose", "SQLite", "Git"},
        "ground_truth_implicit": {"Mobile UI Design", "App Store Optimization"}
    },
    {
        "id": "res_07",
        "domain": "iOS Developer",
        "text": """
Sneha Patel - iOS Engineer
Email: sneha@example.com

[EXPERIENCE]
iOS Developer at MobileLab (2021 - 2023)
- Built fluid declarative user interfaces with reactive state bindings and custom view modifiers.
- Persisted complex offline object graphs and handled background data sync.
- Configured Apple push notification services for user retention messaging.

[SKILLS]
Swift, SwiftUI, iOS Development, Core Data, Xcode
""",
        "ground_truth_explicit": {"Swift", "SwiftUI", "iOS Development", "Core Data"},
        "ground_truth_implicit": {"Push Notifications", "Mobile Offline Sync"}
    },
    {
        "id": "res_08",
        "domain": "Cybersecurity & InfoSec Analyst",
        "text": """
Aditya Joshi - Security Specialist
Email: aditya@example.com

[EXPERIENCE]
Security Analyst at SecOps (2022 - 2024)
- Conducted simulated attacks to identify web application injection vulnerabilities.
- Mitigated automated bot abuse and SQL injection attacks using firewall rules.
- Analyzed network packet traces to detect unauthorized port scanning.

[SKILLS]
Cybersecurity, Penetration Testing, OWASP Top 10, Linux, Python
""",
        "ground_truth_explicit": {"Cybersecurity", "Penetration Testing", "OWASP Top 10", "Linux", "Python"},
        "ground_truth_implicit": {"Vulnerability Assessment", "Network Security"}
    },
    {
        "id": "res_09",
        "domain": "Generative AI & LLM Engineer",
        "text": """
Tanvi Sen - GenAI Specialist
Email: tanvi@example.com

[EXPERIENCE]
AI Engineer at NextGen AI (2023 - Present)
- Architected enterprise semantic retrieval systems querying dense vector chunks.
- Evaluated prompt resilience against adversarial attacks and hallucination.
- Fine-tuned foundation models with parameter-efficient LoRA adapters.

[SKILLS]
Generative AI, Large Language Models, LangChain, ChromaDB, Python
""",
        "ground_truth_explicit": {"Generative AI", "Large Language Models", "LangChain", "ChromaDB", "Python"},
        "ground_truth_implicit": {"Retrieval-Augmented Generation", "Prompt Engineering"}
    },
    {
        "id": "res_10",
        "domain": "QA Automation Engineer",
        "text": """
Karan Malhotra - SDET
Email: karan@example.com

[EXPERIENCE]
QA Automation Lead at QualityFirst (2020 - 2023)
- Automated cross-browser end-to-end regression test suites simulating customer checkouts.
- Automated API contract assertions and status code validations in CI builds.
- Wrote failing unit tests first adhering strictly to red-green-refactor cycles.

[SKILLS]
Cypress, Playwright, Jest, JavaScript, CI/CD, Git
""",
        "ground_truth_explicit": {"Cypress", "Playwright", "Jest", "JavaScript", "CI/CD", "Git"},
        "ground_truth_implicit": {"End-to-End Testing", "Test-Driven Development", "Unit Testing"}
    },
    {
        "id": "res_11",
        "domain": "Site Reliability Engineer (SRE)",
        "text": """
Naveen Rao - SRE
Email: naveen@example.com

[EXPERIENCE]
SRE at TechInfrastructure (2021 - 2024)
- Defined Service Level Objectives (SLOs) and monitored error budgets across microservices.
- Scraped real-time system metrics and configured alerts for high memory utilization.
- Coordinated immediate incident containment during production outages.

[SKILLS]
Prometheus, Grafana, Docker, Kubernetes, Linux, Python
""",
        "ground_truth_explicit": {"Prometheus", "Grafana", "Docker", "Kubernetes", "Linux", "Python"},
        "ground_truth_implicit": {"Site Reliability Engineering", "Incident Response"}
    },
    {
        "id": "res_12",
        "domain": "Blockchain Engineer",
        "text": """
Deepak Chawla - Blockchain Developer
Email: deepak@example.com

[EXPERIENCE]
Smart Contract Developer at CryptoLab (2022 - 2024)
- Authored ERC-20 smart contracts and conducted gas optimization audits.
- Implemented cryptographic signature verification and asymmetric key hashing.
- Integrated decentralized web interfaces with browser crypto wallets.

[SKILLS]
Solidity, JavaScript, WebSockets, Git, Node.js
""",
        "ground_truth_explicit": {"Solidity", "JavaScript", "WebSockets", "Git", "Node.js"},
        "ground_truth_implicit": {"Cryptography"}
    },
    {
        "id": "res_13",
        "domain": "Distributed Systems Engineer (Golang)",
        "text": """
Ananya Gupta - Systems Engineer
Email: ananya@example.com

[EXPERIENCE]
Systems Engineer at DistributedNet (2022 - Present)
- Built low-latency network communication services utilizing Protocol Buffer contracts.
- Prevented thread race conditions by coordinating mutex locks and channels.
- Engineered resilient multi-region architectures with automatic failover.

[SKILLS]
Go, gRPC, Docker, Linux, Git
""",
        "ground_truth_explicit": {"Go", "gRPC", "Docker", "Linux", "Git"},
        "ground_truth_implicit": {"Distributed Systems", "Concurrency", "High Availability"}
    },
    {
        "id": "res_14",
        "domain": "Enterprise Java Architect",
        "text": """
Rajesh Kothari - Enterprise Java Architect
Email: rajesh@example.com

[EXPERIENCE]
Lead Java Engineer at FinanceCore (2019 - 2024)
- Engineered enterprise banking microservices using dependency injection and Spring Data.
- Encapsulated financial business logic using clean ports and adapters architecture.
- Mentored junior engineers and conducted weekly architecture reviews.

[SKILLS]
Java, Spring Boot, PostgreSQL, Microservices, REST API, Git
""",
        "ground_truth_explicit": {"Java", "Spring Boot", "PostgreSQL", "Microservices", "REST API", "Git"},
        "ground_truth_implicit": {"Clean Architecture", "Mentoring", "Team Leadership"}
    },
    {
        "id": "res_15",
        "domain": "UI/UX & Frontend Designer",
        "text": """
Simran Kaur - Frontend & UI Designer
Email: simran@example.com

[EXPERIENCE]
UI/UX Developer at CreativeDesign (2021 - 2024)
- Crafted clickable interactive user prototypes and structured component kits.
- Redesigned customer checkout funnels resulting in a 40% decrease in user drop-off.
- Built accessible responsive web interfaces complying with WCAG guidelines.

[SKILLS]
Figma, React, Tailwind CSS, HTML, CSS, JavaScript
""",
        "ground_truth_explicit": {"Figma", "React", "Tailwind CSS", "HTML", "CSS", "JavaScript"},
        "ground_truth_implicit": {"UI/UX Design", "Prototyping", "Accessibility"}
    },
    {
        "id": "res_16",
        "domain": "Product Manager & Scrum Master",
        "text": """
Manish Saxena - Technical Product Manager
Email: manish@example.com

[EXPERIENCE]
Product Manager at SaaSWorks (2020 - 2023)
- Defined multi-quarter product roadmaps and aligned cross-functional squad milestones.
- Facilitated sprint planning, backlog grooming, and tracked team sprint velocity.
- Authored detailed user stories with testable Given-When-Then criteria.

[SKILLS]
Product Management, Agile, Scrum, JIRA, Confluence
""",
        "ground_truth_explicit": {"Product Management", "Agile", "Scrum", "JIRA", "Confluence"},
        "ground_truth_implicit": {"Sprint Planning", "User Stories", "Stakeholder Management"}
    },
    {
        "id": "res_17",
        "domain": "Database Administrator (DBA)",
        "text": """
Suresh Nair - DBA & Data Modeler
Email: suresh@example.com

[EXPERIENCE]
Database Administrator at DataStore Inc (2018 - 2023)
- Managed automated database backups, replication monitoring, and transaction lock analysis.
- Designed dimensional star schemas and slowly changing dimensions (SCD).
- Optimized slow SQL queries with indexes and EXPLAIN ANALYZE execution plans.

[SKILLS]
PostgreSQL, MySQL, SQL, Linux, Bash Scripting
""",
        "ground_truth_explicit": {"PostgreSQL", "MySQL", "SQL", "Linux", "Shell Scripting"},
        "ground_truth_implicit": {"Database Management", "Data Modeling"}
    },
    {
        "id": "res_18",
        "domain": "Computer Vision & Deep Learning",
        "text": """
Pooja Bhatt - Computer Vision Engineer
Email: pooja@example.com

[EXPERIENCE]
CV Engineer at VisionAI (2022 - 2024)
- Built convolutional neural network models for real-time video object detection.
- Preprocessed video feeds, calibrated camera lenses, and extracted contours.
- Deployed high-throughput model inference endpoints on GPU servers.

[SKILLS]
Python, PyTorch, OpenCV, Computer Vision, Deep Learning, Docker
""",
        "ground_truth_explicit": {"Python", "PyTorch", "OpenCV", "Computer Vision", "Deep Learning", "Docker"},
        "ground_truth_implicit": {"Model Deployment"}
    },
    {
        "id": "res_19",
        "domain": "Embedded Systems Engineer",
        "text": """
Harsh Vardhan - Embedded Software Engineer
Email: harsh@example.com

[EXPERIENCE]
Embedded Systems Engineer at MicroTech (2021 - 2024)
- Developed microcontroller firmware interacting directly with memory hardware registers.
- Optimized low-level memory allocation routines with strict resource budgets.
- Wrote automated hardware test routines using Python serial interfaces.

[SKILLS]
C++, C, Python, Linux, Git
""",
        "ground_truth_explicit": {"C++", "C", "Python", "Linux", "Git"},
        "ground_truth_implicit": {"Concurrency"}
    },
    {
        "id": "res_20",
        "domain": "BI & Data Analyst",
        "text": """
Meera Reddy - Business Intelligence Analyst
Email: meera@example.com

[EXPERIENCE]
BI Analyst at RetailAnalytics (2021 - 2024)
- Built interactive executive dashboards tracking customer acquisition funnels and revenue KPIs.
- Authored complex multi-table SQL joins and window partition calculations.
- Designed randomized split tests and calculated conversion lift with statistical p-values.

[SKILLS]
Power BI, Tableau, SQL, Excel, Python
""",
        "ground_truth_explicit": {"Power BI", "Tableau", "SQL", "Excel", "Python"},
        "ground_truth_implicit": {"Data Analysis", "A/B Testing"}
    }
]


def compute_metrics(
    predictions: Set[str],
    ground_truth: Set[str]
) -> Dict[str, float]:
    """Computes Precision, Recall, and F1-Score."""
    preds_norm = {p.lower() for p in predictions}
    gt_norm = {g.lower() for g in ground_truth}

    true_positives = len(preds_norm & gt_norm)
    false_positives = len(preds_norm - gt_norm)
    false_negatives = len(gt_norm - preds_norm)

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": true_positives,
        "fp": false_positives,
        "fn": false_negatives
    }


def evaluate_two_layer_pipeline(
    extractor: Optional[TwoLayerSkillExtractor] = None,
    thresholds: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Runs systematic evaluation across the 20 benchmark resumes.
    Reports:
    - Layer 1 (Explicit) Precision, Recall, F1
    - Layer 2 (Implicit) Threshold Tuning Sweep Table [0.40 - 0.65]
    - Combined Two-Layer Pipeline Performance
    """
    if extractor is None:
        extractor = TwoLayerSkillExtractor()

    sweep_thresholds = thresholds or [0.40, 0.45, 0.50, 0.52, 0.55, 0.60, 0.65]

    # 1. Evaluate Explicit Layer Alone
    explicit_preds_all: List[Set[str]] = []
    explicit_gt_all: List[Set[str]] = []

    for item in LABELED_RESUMES:
        raw_text = item["text"]
        gt_exp = item["ground_truth_explicit"]
        extracted = extractor.extract_skills(raw_text, include_implicit=False)
        pred_skills = {s["name"] for s in extracted}
        explicit_preds_all.append(pred_skills)
        explicit_gt_all.append(gt_exp)

    # Aggregate explicit metrics
    all_tp_exp = sum(len({p.lower() for p in p_set} & {g.lower() for g in g_set}) for p_set, g_set in zip(explicit_preds_all, explicit_gt_all))
    all_fp_exp = sum(len({p.lower() for p in p_set} - {g.lower() for g in g_set}) for p_set, g_set in zip(explicit_preds_all, explicit_gt_all))
    all_fn_exp = sum(len({g.lower() for g in g_set} - {p.lower() for p in p_set}) for p_set, g_set in zip(explicit_preds_all, explicit_gt_all))

    p_exp = all_tp_exp / (all_tp_exp + all_fp_exp) if (all_tp_exp + all_fp_exp) > 0 else 0.0
    r_exp = all_tp_exp / (all_tp_exp + all_fn_exp) if (all_tp_exp + all_fn_exp) > 0 else 0.0
    f1_exp = (2 * p_exp * r_exp) / (p_exp + r_exp) if (p_exp + r_exp) > 0 else 0.0

    explicit_report = {
        "precision": round(p_exp, 4),
        "recall": round(r_exp, 4),
        "f1": round(f1_exp, 4),
        "total_true_positives": all_tp_exp,
        "total_false_positives": all_fp_exp,
        "total_false_negatives": all_fn_exp
    }

    # 2. Evaluate Implicit Layer Across Threshold Sweep
    threshold_results: List[Dict[str, Any]] = []

    for th in sweep_thresholds:
        all_tp_imp = 0
        all_fp_imp = 0
        all_fn_imp = 0

        for item in LABELED_RESUMES:
            raw_text = item["text"]
            gt_imp = item["ground_truth_implicit"]
            gt_exp = item["ground_truth_explicit"]

            # Exclude explicit skills from implicit evaluation
            imp_skills = extractor.implicit_matcher.detect_implicit_skills(
                resume_data=raw_text,
                explicit_skills=gt_exp,
                threshold=th
            )
            pred_imp = {s["name"] for s in imp_skills}

            p_set = {p.lower() for p in pred_imp}
            g_set = {g.lower() for g in gt_imp}

            all_tp_imp += len(p_set & g_set)
            all_fp_imp += len(p_set - g_set)
            all_fn_imp += len(g_set - p_set)

        p_imp = all_tp_imp / (all_tp_imp + all_fp_imp) if (all_tp_imp + all_fp_imp) > 0 else 0.0
        r_imp = all_tp_imp / (all_tp_imp + all_fn_imp) if (all_tp_imp + all_fn_imp) > 0 else 0.0
        f1_imp = (2 * p_imp * r_imp) / (p_imp + r_imp) if (p_imp + r_imp) > 0 else 0.0

        threshold_results.append({
            "threshold": th,
            "precision": round(p_imp, 4),
            "recall": round(r_imp, 4),
            "f1": round(f1_imp, 4),
            "tp": all_tp_imp,
            "fp": all_fp_imp,
            "fn": all_fn_imp
        })

    # Pick optimal threshold (highest F1)
    best_threshold_row = max(threshold_results, key=lambda x: x["f1"])
    optimal_threshold = best_threshold_row["threshold"]

    # 3. Evaluate Combined Two-Layer Pipeline at Optimal Threshold
    all_tp_comb = 0
    all_fp_comb = 0
    all_fn_comb = 0

    for item in LABELED_RESUMES:
        raw_text = item["text"]
        gt_combined = item["ground_truth_explicit"] | item["ground_truth_implicit"]

        extracted = extractor.extract_skills(raw_text, implicit_threshold=optimal_threshold)
        pred_combined = {s["name"] for s in extracted}

        p_set = {p.lower() for p in pred_combined}
        g_set = {g.lower() for g in gt_combined}

        all_tp_comb += len(p_set & g_set)
        all_fp_comb += len(p_set - g_set)
        all_fn_comb += len(g_set - p_set)

    p_comb = all_tp_comb / (all_tp_comb + all_fp_comb) if (all_tp_comb + all_fp_comb) > 0 else 0.0
    r_comb = all_tp_comb / (all_tp_comb + all_fn_comb) if (all_tp_comb + all_fn_comb) > 0 else 0.0
    f1_comb = (2 * p_comb * r_comb) / (p_comb + r_comb) if (p_comb + r_comb) > 0 else 0.0

    combined_report = {
        "optimal_threshold": optimal_threshold,
        "precision": round(p_comb, 4),
        "recall": round(r_comb, 4),
        "f1": round(f1_comb, 4),
        "total_true_positives": all_tp_comb,
        "total_false_positives": all_fp_comb,
        "total_false_negatives": all_fn_comb
    }

    return {
        "labeled_resumes_count": len(LABELED_RESUMES),
        "explicit_layer": explicit_report,
        "implicit_layer_sweep": threshold_results,
        "combined_pipeline": combined_report
    }


def format_evaluation_table(eval_results: Dict[str, Any]) -> str:
    """Formats evaluation results as a clean ASCII report."""
    lines: List[str] = []
    lines.append("=" * 72)
    lines.append(" CAREERLENS TWO-LAYER SKILL EXTRACTION: 20-RESUME BENCHMARK EVALUATION ")
    lines.append("=" * 72)
    lines.append(f"Evaluated on {eval_results['labeled_resumes_count']} diverse labeled resumes across 20 domains.")
    lines.append("")

    # Explicit
    exp = eval_results["explicit_layer"]
    lines.append("--- LAYER 1: EXPLICIT KEYWORD & TAXONOMY MATCHER ---")
    lines.append(f"Precision: {exp['precision']:.4f} ({exp['precision']*100:.1f}%) | "
                 f"Recall: {exp['recall']:.4f} ({exp['recall']*100:.1f}%) | "
                 f"F1-Score: {exp['f1']:.4f}")
    lines.append(f"TP: {exp['total_true_positives']} | FP: {exp['total_false_positives']} | FN: {exp['total_false_negatives']}")
    lines.append("")

    # Implicit sweep table
    lines.append("--- LAYER 2: IMPLICIT EMBEDDING MATCHER THRESHOLD SWEEP ---")
    lines.append(f"{'Threshold':<11} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10} | {'TP':<4} | {'FP':<4} | {'FN':<4}")
    lines.append("-" * 72)
    for row in eval_results["implicit_layer_sweep"]:
        marker = " <-- (Optimal)" if row["threshold"] == eval_results["combined_pipeline"]["optimal_threshold"] else ""
        lines.append(f"{row['threshold']:<11.2f} | {row['precision']:<10.4f} | {row['recall']:<10.4f} | {row['f1']:<10.4f} | "
                     f"{row['tp']:<4} | {row['fp']:<4} | {row['fn']:<4}{marker}")
    lines.append("-" * 72)
    lines.append("")

    # Combined
    comb = eval_results["combined_pipeline"]
    lines.append("--- FINAL COMBINED PIPELINE (Explicit + Implicit @ Optimal Threshold) ---")
    lines.append(f"Optimal Cosine Threshold: {comb['optimal_threshold']:.2f}")
    lines.append(f"Precision: {comb['precision']:.4f} ({comb['precision']*100:.1f}%) | "
                 f"Recall: {comb['recall']:.4f} ({comb['recall']*100:.1f}%) | "
                 f"F1-Score: {comb['f1']:.4f}")
    lines.append(f"TP: {comb['total_true_positives']} | FP: {comb['total_false_positives']} | FN: {comb['total_false_negatives']}")
    lines.append("=" * 72)

    return "\n".join(lines)


if __name__ == "__main__":
    print("Running evaluation on 20 labeled benchmark resumes...")
    results = evaluate_two_layer_pipeline()
    report = format_evaluation_table(results)
    print(report)
