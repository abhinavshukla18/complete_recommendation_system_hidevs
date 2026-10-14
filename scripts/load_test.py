"""Simple load test: 10 users hit the running API at the same time.

1. In one terminal start the API:  python -m api.app
2. In a second terminal run:       python -m scripts.load_test
"""
import json
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://127.0.0.1:5000"
CONCURRENT_USERS = 10
REQUESTS_PER_USER = 20


def one_request(user_id):
    """Call /recommend once. Returns (success, milliseconds)."""
    start = time.time()
    url = BASE_URL + "/recommend/" + str(user_id) + "?limit=5"
    try:
        with urllib.request.urlopen(url) as response:
            success = response.status == 200
    except Exception:
        success = False
    return success, (time.time() - start) * 1000


def simulated_user(user_id):
    """One user making several requests in a row."""
    results = []
    for _ in range(REQUESTS_PER_USER):
        results.append(one_request(user_id))
    return results


def main():
    user_ids = list(range(1, CONCURRENT_USERS + 1))

    start = time.time()
    with ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as pool:
        all_results = list(pool.map(simulated_user, user_ids))
    elapsed = time.time() - start

    results = []
    for user_results in all_results:
        results.extend(user_results)

    total = len(results)
    successes = sum(1 for ok, ms in results if ok)
    times = sorted(ms for ok, ms in results)
    average = sum(times) / total
    p95 = times[int(total * 0.95) - 1]

    print("Concurrent users:", CONCURRENT_USERS)
    print("Total requests:", total)
    print("Successful:", successes)
    print("Average response (ms):", round(average, 1))
    print("95th percentile (ms):", round(p95, 1))
    print("Slowest (ms):", round(times[-1], 1))
    print("Throughput (requests/second):", round(total / elapsed, 1))

    average_ok = "met" if average < 500 else "not met"
    rate = total / elapsed
    rate_ok = "met" if rate >= 10 else "not met"

    section = []
    section.append("## Load test")
    section.append("")
    section.append(str(CONCURRENT_USERS) + " simulated users each sent "
                   + str(REQUESTS_PER_USER) + " requests to "
                   "GET /recommend/<user_id>?limit=5 at the same time.")
    section.append("")
    section.append("| Measure | Result | Target |")
    section.append("|---|---|---|")
    section.append("| Total requests | " + str(total) + " | |")
    section.append("| Successful | " + str(successes) + " | all |")
    section.append("| Average response | " + str(round(average, 1))
                   + " ms | under 500 ms (" + average_ok + ") |")
    section.append("| 95th percentile | " + str(round(p95, 1)) + " ms | |")
    section.append("| Slowest | " + str(round(times[-1], 1)) + " ms | |")
    section.append("| Throughput | " + str(round(rate, 1))
                   + " requests/second | 10+ (" + rate_ok + ") |")

    try:
        with urllib.request.urlopen(BASE_URL + "/metrics") as response:
            cache = json.loads(response.read())["cache"]
    except Exception:
        cache = None

    if cache:
        hit_percent = round(cache["hit_rate"] * 100, 1)
        section.append("")
        section.append("Cache effectiveness (from GET /metrics):")
        section.append("")
        section.append("| Cache measure | Value |")
        section.append("|---|---|")
        section.append("| Hits | " + str(cache["hits"]) + " |")
        section.append("| Misses | " + str(cache["misses"]) + " |")
        section.append("| Hit rate | " + str(hit_percent) + "% |")

    try:
        with open("evaluation_report.md") as report_file:
            text = report_file.read()
    except FileNotFoundError:
        text = "# Evaluation Report\n"
    text = text.split("\n## Load test")[0].rstrip() + "\n\n"
    text = text + "\n".join(section) + "\n"
    with open("evaluation_report.md", "w") as report_file:
        report_file.write(text)
    print("Load test results added to evaluation_report.md")


if __name__ == "__main__":
    main()
