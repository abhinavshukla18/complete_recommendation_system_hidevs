"""Evaluate the recommender with a hold-out test.

Run it from the project folder:  python -m scripts.evaluate
"""
import os

# Use a temporary in-memory database so your real one is never touched.
# This must be set before data.database is imported.
os.environ["DATABASE_URL"] = "sqlite://"

from data.database import Base, db_engine, get_session, init_db  # noqa: E402
from engine.orchestrator import RecommendationOrchestrator  # noqa: E402
from engine.evaluator import RecommendationEvaluator  # noqa: E402
from scripts.seed_data import seed  # noqa: E402
from tests.test_data import INTERACTIONS  # noqa: E402


def split_interactions():
    """Hide each user's last liked item.

    Returns (training, held_out): the interactions the engine may see,
    and a dict of user_id -> the one content_id we hid.
    """
    liked = {}
    for user_id, content_id, kind, rating in INTERACTIONS:
        is_positive = (kind == "like"
                       or kind == "complete"
                       or (kind == "rating" and rating >= 4))
        if is_positive:
            liked.setdefault(user_id, []).append(content_id)

    held_out = {}
    for user_id, items in liked.items():
        if len(items) >= 2:
            held_out[user_id] = items[-1]

    training = []
    for row in INTERACTIONS:
        user_id, content_id, kind, rating = row
        if held_out.get(user_id) == content_id:
            continue  # hide every interaction this user had with it
        training.append(row)
    return training, held_out


def build_orchestrator(training):
    """Make a fresh database holding only the training interactions."""
    init_db()
    Base.metadata.drop_all(db_engine)
    Base.metadata.create_all(db_engine)
    session = get_session()
    seed(session, training)
    return RecommendationOrchestrator(session)


def main():
    training, held_out = split_interactions()
    print("Training interactions:", len(training))
    print("Users with a hidden item:", len(held_out))

    orchestrator = build_orchestrator(training)

    recommendations = {}
    ground_truth = {}
    for user_id, hidden_item in held_out.items():
        results = orchestrator.get_recommendations(user_id, 5)
        recommendations[user_id] = [item["content_id"] for item in results]
        ground_truth[user_id] = [hidden_item]

    evaluator = RecommendationEvaluator()
    scores = evaluator.evaluate_all(recommendations, ground_truth, 5)

    print("Precision@5:", round(scores["precision_at_k"], 3))
    print("Recall@5:", round(scores["recall_at_k"], 3))
    print("NDCG@5:", round(scores["ndcg_at_k"], 3))
    print("Users evaluated:", scores["users_evaluated"])

    lines = []
    lines.append("# Evaluation Report")
    lines.append("")
    lines.append("Hold-out test: each user's last positive item (a like, a "
                 "completion, or a rating of 4-5) was hidden, and the engine "
                 "had to bring it back in its top 5.")
    lines.append("")
    lines.append("| Metric | Score |")
    lines.append("|---|---|")
    lines.append("| Precision@5 | " +
                 str(round(scores["precision_at_k"], 3)) + " |")
    lines.append("| Recall@5 | " + str(round(scores["recall_at_k"], 3)) + " |")
    lines.append("| NDCG@5 | " + str(round(scores["ndcg_at_k"], 3)) + " |")
    lines.append("| Users evaluated | " +
                 str(scores["users_evaluated"]) + " |")
    lines.append("")
    lines.append("## Per-user results")
    lines.append("")
    lines.append("| User | Hidden item | Top 5 recommended | Found | NDCG@5 |")
    lines.append("|---|---|---|---|---|")
    for user_id in held_out:
        recs = recommendations[user_id]
        hidden = held_out[user_id]
        found = "yes" if hidden in recs else "no"
        ndcg = round(evaluator.ndcg_at_k(recs, [hidden], 5), 3)
        lines.append("| " + str(user_id) + " | " + str(hidden) + " | "
                     + str(recs) + " | " + found + " | " + str(ndcg) + " |")

    with open("evaluation_report.md", "w") as report_file:
        report_file.write("\n".join(lines) + "\n")
    print("Report saved to evaluation_report.md")


if __name__ == "__main__":
    main()
