class RecommendationScorer:
    """Scores items using several weighted scoring functions."""

    def __init__(self):
        self.scorers = {}    # name -> {"function": ..., "weight": ...}

    def add_scorer(self, name, function, weight):
        """Register a scoring function (must return a number from 0 to 1)."""
        if weight < 0:
            raise ValueError("weight cannot be negative")
        self.scorers[name] = {"function": function, "weight": weight}

    def calculate_score(self, user_id, item_id, context=None):
        """Weighted average of all scoring functions, between 0 and 1."""
        if context is None:
            context = {}

        # Edge case: no scoring functions added yet
        if len(self.scorers) == 0:
            return 0.0

        total = 0
        total_weight = 0
        for name, info in self.scorers.items():
            score = info["function"](user_id, item_id, context)
            # keep each score between 0 and 1
            score = max(0.0, min(1.0, score))
            total = total + score * info["weight"]
            total_weight = total_weight + info["weight"]

        # Edge case: all weights are 0
        if total_weight == 0:
            return 0.0

        return total / total_weight

    def explain(self, user_id, item_id, context=None):
        """Name the scoring factor that contributed most to an item's score."""
        if context is None:
            context = {}

        best_name = None
        best_value = -1
        best_score = 0
        for name, info in self.scorers.items():
            score = info["function"](user_id, item_id, context)
            score = max(0.0, min(1.0, score))
            # how much this factor contributed
            value = score * info["weight"]
            if value > best_value:
                best_value = value
                best_name = name
                best_score = score

        if best_name is None:
            return "No scoring factors were set"
        return ("Recommended mainly because of " + best_name
                + " (score " + str(round(best_score, 2)) + ")")

    def rank_candidates(self, user_id, candidates, limit=10, context=None):
        """Score every candidate and return the top ones, best first."""
        # Edge case: nothing to rank
        if not candidates:
            return []

        results = []
        for item in candidates:
            score = self.calculate_score(user_id, item, context)
            reason = self.explain(user_id, item, context)
            results.append({"item": item, "score": score, "reason": reason})

        # Highest score first (ties broken by item name)
        results.sort(key=lambda r: (-r["score"], r["item"]))

        return results[:limit]
