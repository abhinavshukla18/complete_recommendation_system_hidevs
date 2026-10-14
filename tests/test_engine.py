"""Tests for the engine: Day 29 modules and the orchestrator."""
import pytest

from engine.candidate_gen import CandidateGenerator
from engine.evaluator import RecommendationEvaluator
from engine.orchestrator import (ContentNotFoundError,
                                 RecommendationOrchestrator,
                                 UserNotFoundError)
from engine.scorer import RecommendationScorer
from engine.similarity import SimilarityCalculator

USER_RATINGS = {
    "u1": {"i1": 5, "i2": 3, "i3": 4},
    "u2": {"i1": 4, "i2": 2, "i4": 5},
    "u3": {},
}
ITEMS = {
    "i1": {"tags": {"action", "thriller"}},
    "i2": {"tags": {"comedy"}},
    "i3": {"tags": {"action", "drama"}},
    "i4": {"tags": {"comedy", "romance"}},
    "i5": {"tags": {"action", "comedy"}},
}


# ----- similarity -----

def test_cosine_similarity():
    calc = SimilarityCalculator()
    assert calc.cosine_similarity([5, 3, 4], [5, 3, 4]) == pytest.approx(1.0)
    assert calc.cosine_similarity([1, 0], [0, 1]) == 0.0
    assert calc.cosine_similarity([0, 0, 0], [1, 2, 3]) == 0.0
    assert calc.cosine_similarity([], []) == 0.0
    assert calc.cosine_similarity([1, 2], [1, 2, 3]) == 0.0


def test_jaccard_similarity():
    calc = SimilarityCalculator()
    assert calc.jaccard_similarity({"a", "b", "c"}, {"a", "c", "d"}) == 0.5
    assert calc.jaccard_similarity({"a"}, {"b"}) == 0.0
    assert calc.jaccard_similarity(set(), set()) == 0.0
    assert calc.jaccard_similarity(set(), {"a"}) == 0.0


def test_pearson_correlation():
    calc = SimilarityCalculator()
    assert calc.pearson_correlation([1, 2, 3], [2, 4, 6]) == pytest.approx(1.0)
    reversed_ = calc.pearson_correlation([1, 2, 3], [3, 2, 1])
    assert reversed_ == pytest.approx(-1.0)
    assert calc.pearson_correlation([4, 4, 4], [1, 2, 3]) == 0.0
    assert calc.pearson_correlation([], []) == 0.0


# ----- candidate generator -----

def test_candidate_strategies():
    gen = CandidateGenerator(USER_RATINGS, ITEMS)
    assert gen.popularity_candidates() == ["i1", "i3", "i4"]
    assert gen.content_based_candidates("u1") == ["i5"]
    assert gen.collaborative_candidates("u1") == ["i4"]
    assert gen.hybrid_candidates("u1") == ["i4", "i5"]


def test_candidates_cold_start_and_limit():
    gen = CandidateGenerator(USER_RATINGS, ITEMS)
    assert gen.hybrid_candidates("u3") == ["i1", "i3", "i4"]
    assert gen.hybrid_candidates("unknown") == ["i1", "i3", "i4"]
    assert CandidateGenerator({}, {}).popularity_candidates() == []
    small = CandidateGenerator(USER_RATINGS, ITEMS, limit=1)
    assert small.hybrid_candidates("u3") == ["i1"]


# ----- scorer -----

def test_scorer_weighted_average():
    scorer = RecommendationScorer()
    scorer.add_scorer("relevance", lambda u, i, c: 0.8, 2)
    scorer.add_scorer("popularity", lambda u, i, c: 0.4, 1)
    assert scorer.calculate_score("u1", "i1") == pytest.approx(2 / 3, abs=1e-3)


def test_scorer_edge_cases():
    assert RecommendationScorer().calculate_score("u1", "i1") == 0.0
    scorer = RecommendationScorer()
    scorer.add_scorer("wild", lambda u, i, c: 5, 1)
    assert scorer.calculate_score("u1", "i1") == 1.0      # clamped to 1
    zero = RecommendationScorer()
    zero.add_scorer("none", lambda u, i, c: 0.5, 0)
    assert zero.calculate_score("u1", "i1") == 0.0
    with pytest.raises(ValueError):
        scorer.add_scorer("bad", lambda u, i, c: 1, -1)


def test_scorer_ranking_and_explanation():
    relevance = {"i1": 0.5, "i2": 0.9, "i3": 0.6}
    popularity = {"i1": 0.9, "i2": 0.2, "i3": 0.5}
    scorer = RecommendationScorer()
    scorer.add_scorer("relevance", lambda u, i, c: relevance[i], 2)
    scorer.add_scorer("popularity", lambda u, i, c: popularity[i], 1)
    top = scorer.rank_candidates("u1", ["i1", "i2", "i3"], limit=2)
    assert [r["item"] for r in top] == ["i2", "i1"]
    assert "relevance" in top[0]["reason"]
    assert scorer.rank_candidates("u1", [], limit=2) == []
    assert RecommendationScorer().explain("u1", "i1") == (
        "No scoring factors were set")


# ----- evaluator -----

def test_evaluator_metrics():
    ev = RecommendationEvaluator()
    recs = ["i2", "i5", "i1", "i9"]
    liked = {"i1", "i2", "i3", "i4"}
    assert ev.precision_at_k(recs, liked, 3) == pytest.approx(2 / 3)
    assert ev.recall_at_k(recs, liked, 3) == 0.5
    assert ev.ndcg_at_k(recs, liked, 3) == pytest.approx(0.7039, abs=1e-4)
    assert ev.precision_at_k([], liked, 3) == 0.0
    assert ev.recall_at_k(recs, set(), 3) == 0.0
    assert ev.ndcg_at_k(recs, liked, 0) == 0.0


def test_evaluate_all_skips_missing_ground_truth():
    ev = RecommendationEvaluator()
    result = ev.evaluate_all(
        {"u1": ["i2", "i5", "i1", "i9"], "u2": ["i3", "i4"], "u3": ["i1"]},
        {"u1": {"i1", "i2", "i3", "i4"}, "u2": {"i3"}},
        3)
    assert result["users_evaluated"] == 2
    assert result["precision_at_k"] == pytest.approx(0.5)
    assert result["recall_at_k"] == pytest.approx(0.75)
    assert ev.evaluate_all({}, {}, 3)["users_evaluated"] == 0


# ----- orchestrator (uses the seeded database) -----

def test_orchestrator_loads_data(session):
    reco = RecommendationOrchestrator(session)
    assert len(reco.items) == 24
    assert len(reco.user_ratings) == 11
    assert reco.user_ratings[1] == {1: 5, 2: 5, 3: 4, 4: 4, 6: 5, 5: 3}
    assert reco.items[4]["tags"] == {"python", "machine learning",
                                     "statistics"}
    assert 12 not in reco.user_ratings


def test_recommendations_make_sense(session):
    reco = RecommendationOrchestrator(session)
    results = reco.get_recommendations(1, 5)
    assert len(results) == 5
    assert results[0]["title"] == "Deep Learning Basics"
    seen = set(reco.user_ratings[1])
    for entry in results:
        assert entry["content_id"] not in seen
        assert 0.0 <= entry["score"] <= 1.0
        assert entry["reason"].startswith("Recommended because")
    scores = [entry["score"] for entry in results]
    assert scores == sorted(scores, reverse=True)


def test_cold_start_user(session):
    reco = RecommendationOrchestrator(session)
    results = reco.get_recommendations(12, 5)
    assert len(results) == 5
    assert results[0]["title"] == "Python for Beginners"
    assert "learners like you" not in results[0]["reason"]


def test_unknown_user_raises(session):
    reco = RecommendationOrchestrator(session)
    with pytest.raises(UserNotFoundError):
        reco.get_recommendations(999)


def test_cache_hits_and_stats(session):
    reco = RecommendationOrchestrator(session)
    first = reco.get_recommendations(1, 3)
    second = reco.get_recommendations(1, 3)
    assert first == second
    assert reco.cache_stats() == {"hits": 1, "misses": 1, "size": 1,
                                  "hit_rate": 0.5}


def test_feedback_changes_recommendations(session):
    reco = RecommendationOrchestrator(session)
    before = reco.get_recommendations(12, 3)
    reco.record_feedback(12, 16, "rating", 5)
    assert reco.cache_stats()["size"] == 0           # cache was cleared
    after = reco.get_recommendations(12, 3)
    assert before != after
    assert 16 not in [entry["content_id"] for entry in after]
    assert "learners like you" in after[0]["reason"]


def test_feedback_errors(session):
    reco = RecommendationOrchestrator(session)
    with pytest.raises(UserNotFoundError):
        reco.record_feedback(999, 1, "like")
    with pytest.raises(ContentNotFoundError):
        reco.record_feedback(1, 999, "like")
    with pytest.raises(ValueError):
        reco.record_feedback(1, 1, "dance")
    with pytest.raises(ValueError):
        reco.record_feedback(1, 1, "rating", 9)
