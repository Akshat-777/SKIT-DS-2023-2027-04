"""Warm-model benchmark for single text, batch, and one ParsedResume payload."""

import argparse
import copy
import platform
import statistics
import time

from fastapi.testclient import TestClient

from embedding_service.app.main import create_app


RESUME = {
    "resume_id": "benchmark-resume",
    "sections": {"summary": "Data scientist with Python and machine learning experience.",
                 "projects": "Built a document classification project using NLP."},
    "experience": [{"title": "Data Scientist", "company": "Example Labs",
                     "bullets": ["Trained classification models in Python.",
                                 "Built feature pipelines using SQL and Pandas.",
                                 "Presented model results to product stakeholders."]}],
    "skills": [{"name": "Python"}, {"name": "Machine Learning"}, {"name": "SQL"}, {"name": "Pandas"}],
    "raw_text": "Data scientist focused on applied machine learning and analytics." * 20,
}


def measure(client, path, payload, iterations):
    samples = []
    for iteration in range(iterations):
        request_payload = copy.deepcopy(payload)
        if path == "/embed":
            request_payload["text"] += f" Benchmark sample {iteration}."
        elif path == "/embed/batch":
            request_payload["texts"] = [text + f" Sample {iteration}." for text in request_payload["texts"]]
        else:
            request_payload["raw_text"] += f" Benchmark sample {iteration}."
        started = time.perf_counter()
        response = client.post(path, json=request_payload)
        response.raise_for_status()
        samples.append((time.perf_counter() - started) * 1000)
    return statistics.mean(samples), sorted(samples)[min(len(samples) - 1, int(0.95 * len(samples)))]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=30)
    args = parser.parse_args()
    app = create_app()
    with TestClient(app) as client:
        rows = [
            ("Single text", "/embed", {"text": "Python machine learning engineer builds APIs."}),
            ("Batch of 16", "/embed/batch", {"texts": ["Python engineer builds APIs."] * 16}),
            ("ParsedResume", "/embed/resume", RESUME),
        ]
        print(f"Device: {client.get('/model-info').json()['device']} | CPU: {platform.processor()} | iterations: {args.iterations}")
        print("| Request | Mean latency (ms) | p95 latency (ms) |")
        print("|---|---:|---:|")
        for label, path, payload in rows:
            mean, p95 = measure(client, path, payload, args.iterations)
            print(f"| {label} | {mean:.2f} | {p95:.2f} |")


if __name__ == "__main__":
    main()
