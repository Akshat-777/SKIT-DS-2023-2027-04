"""Concurrent HTTP load check for a running embedding service."""

import argparse
import concurrent.futures
import statistics
import time

import requests


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    def one(_index):
        text = ("Python machine learning engineer builds reliable data services. " * 8
                + f"Unique request number {_index}.")
        started = time.perf_counter()
        response = requests.post(f"{args.url.rstrip('/')}/embed", json={"text": text}, timeout=60)
        response.raise_for_status()
        return (time.perf_counter() - started) * 1000

    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        latencies = list(pool.map(one, range(args.requests)))
    elapsed = time.perf_counter() - started
    ordered = sorted(latencies)
    p95 = ordered[min(len(ordered) - 1, int(0.95 * len(ordered)))]
    print(f"Requests: {len(latencies)} | workers: {args.workers} | elapsed: {elapsed:.2f}s")
    print(f"Throughput: {len(latencies)/elapsed:.2f} req/s | mean: {statistics.mean(latencies):.2f} ms | p95: {p95:.2f} ms")


if __name__ == "__main__":
    main()
