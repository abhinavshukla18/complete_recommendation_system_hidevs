# Evaluation Report

Hold-out test: each user's last positive item (a like, a completion, or a rating of 4-5) was hidden, and the engine had to bring it back in its top 5.

| Metric | Score |
|---|---|
| Precision@5 | 0.145 |
| Recall@5 | 0.727 |
| NDCG@5 | 0.591 |
| Users evaluated | 11 |

## Per-user results

| User | Hidden item | Top 5 recommended | Found | NDCG@5 |
|---|---|---|---|---|
| 1 | 6 | [24, 16, 6, 10, 7] | yes | 0.5 |
| 2 | 24 | [24, 16, 6, 10, 7] | yes | 1.0 |
| 3 | 8 | [6, 4, 8, 16, 24] | yes | 0.5 |
| 4 | 18 | [15, 1, 2, 16, 4] | no | 0.0 |
| 5 | 17 | [17, 16, 1, 4, 7] | yes | 1.0 |
| 6 | 18 | [1, 2, 15, 4, 24] | no | 0.0 |
| 7 | 10 | [10, 1, 4, 2, 24] | yes | 1.0 |
| 8 | 23 | [23, 1, 11, 2, 16] | yes | 1.0 |
| 9 | 18 | [6, 4, 24, 5, 10] | no | 0.0 |
| 10 | 6 | [5, 16, 6, 10, 7] | yes | 0.5 |
| 11 | 12 | [12, 19, 16, 21, 17] | yes | 1.0 |

## Load test

10 simulated users each sent 20 requests to GET /recommend/<user_id>?limit=5 at the same time.

| Measure | Result | Target |
|---|---|---|
| Total requests | 200 | |
| Successful | 200 | all |
| Average response | 119.7 ms | under 500 ms (met) |
| 95th percentile | 229.1 ms | |
| Slowest | 699.0 ms | |
| Throughput | 79.8 requests/second | 10+ (met) |

Cache effectiveness (from GET /metrics):

| Cache measure | Value |
|---|---|
| Hits | 190 |
| Misses | 10 |
| Hit rate | 95.0% |
