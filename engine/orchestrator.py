"""Main recommendation engine: connects the database to the Day 29 modules."""
from data.repositories import (ContentRepository, ContentSkillRepository,
                               InteractionRepository, SkillRepository,
                               UserRepository, UserSkillRepository)
from engine.candidate_gen import CandidateGenerator
from engine.scorer import RecommendationScorer
from engine.similarity import SimilarityCalculator

# How interactions without a number are turned into a 1-5 rating
INTERACTION_RATINGS = {"like": 5, "complete": 4, "view": 3}

CANDIDATE_LIMIT = 30      # max items each strategy may suggest
STRATEGY_COUNT = 4        # collaborative, content-based, skill-based, popular

# How much each scoring factor matters (they add up to 1.0)
SCORER_WEIGHTS = {"relevance": 0.5, "agreement": 0.3, "popularity": 0.2}

# Plain-English reason for each strategy
SOURCE_REASONS = {
    "collaborative": "learners like you liked it",
    "content-based": "it is similar to content you liked",
    "skill-based": "it teaches skills you are interested in",
    "popular": "it is popular with learners",
}


class UserNotFoundError(Exception):
    """Raised when a recommendation is requested for an unknown user."""


class ContentNotFoundError(Exception):
    """Raised when feedback refers to content that does not exist."""


class RecommendationOrchestrator:
    """Loads data from the database and produces recommendations."""

    def __init__(self, session):
        self.users = UserRepository(session)
        self.user_skills = UserSkillRepository(session)
        self.contents = ContentRepository(session)
        self.content_skills = ContentSkillRepository(session)
        self.interactions = InteractionRepository(session)
        self.skills = SkillRepository(session)
        self.similarity = SimilarityCalculator()
        self.items = {}          # content id -> {"tags": set of skill names}
        self.user_ratings = {}   # user id -> {content id: rating 1-5}
        self.popularity = {}     # content id -> popularity 0-1
        self.declared = {}       # user id -> skills and interests they stated
        self.generator = None
        self.cache = {}          # (user id, limit) -> recommendations
        self.cache_hits = 0
        self.cache_misses = 0
        self.scorer = self._build_scorer()
        self.load_data()

    def load_data(self):
        """Read content and interactions from the database into dictionaries.

        These are the same dictionary shapes the Day 29 modules expect.
        """
        skill_names = {skill.id: skill.name for skill in self.skills.get_all()}

        self.items = {}
        self.popularity = {}
        for content in self.contents.get_all():
            tags = set()
            for skill_id in self.content_skills.get_skill_ids(content.id):
                tags.add(skill_names[skill_id])
            self.items[content.id] = {"tags": tags}
            self.popularity[content.id] = content.popularity

        self.declared = {}
        known = set(skill_names.values())
        for user in self.users.get_all():
            names = set()
            for link in self.user_skills.get_for_user(user.id):
                names.add(skill_names[link.skill_id])
            for word in (user.interests or "").split(","):
                word = word.strip().lower()
                if word in known:
                    names.add(word)
            self.declared[user.id] = names

        self.user_ratings = {}
        history = sorted(self.interactions.get_all(), key=lambda i: i.id)
        for interaction in history:                  # oldest first
            rating = self._to_rating(interaction)
            if rating is None:
                continue
            user_items = self.user_ratings.setdefault(interaction.user_id, {})
            is_view = interaction.type == "view"
            if is_view and interaction.content_id in user_items:
                continue        # a view never replaces a stronger signal
            user_items[interaction.content_id] = rating

        self.generator = CandidateGenerator(self.user_ratings, self.items,
                                            limit=CANDIDATE_LIMIT)

    def _to_rating(self, interaction):
        """Turn one interaction into a 1-5 rating (None if it has no value)."""
        if interaction.type == "rating":
            return interaction.rating
        return INTERACTION_RATINGS.get(interaction.type)

    # ----- scoring -----

    def _build_scorer(self):
        """Create the scorer and register the three scoring factors."""
        scorer = RecommendationScorer()
        scorer.add_scorer("relevance", self._relevance_score,
                          SCORER_WEIGHTS["relevance"])
        scorer.add_scorer("agreement", self._agreement_score,
                          SCORER_WEIGHTS["agreement"])
        scorer.add_scorer("popularity", self._popularity_score,
                          SCORER_WEIGHTS["popularity"])
        return scorer

    def _relevance_score(self, user_id, item_id, context):
        """How much the item's skills overlap with the user's profile."""
        return self.similarity.jaccard_similarity(
            context["profile"], self.items[item_id]["tags"])

    def _agreement_score(self, user_id, item_id, context):
        """How many strategies suggested this item (more = better)."""
        return len(context["sources"][item_id]) / STRATEGY_COUNT

    def _popularity_score(self, user_id, item_id, context):
        """How popular the item is overall."""
        return self.popularity.get(item_id, 0.0)

    # ----- recommendations -----

    def _compute_recommendations(self, user_id, limit):
        """Work out the top recommendations for a user (no caching)."""
        if self.users.get(user_id) is None:
            raise UserNotFoundError("user %s not found" % user_id)

        seen = set(self.user_ratings.get(user_id, {}))
        sources = self._collect_candidates(user_id, seen)
        if not sources:
            return []

        context = {"profile": self._profile(user_id), "sources": sources}
        ranked = self.scorer.rank_candidates(user_id, list(sources),
                                             limit, context)

        results = []
        for entry in ranked:
            content = self.contents.get(entry["item"])
            results.append({
                "content_id": content.id,
                "title": content.title,
                "score": round(entry["score"], 4),
                "reason": self._explain(sources[entry["item"]]),
            })
        return results

    def _collect_candidates(self, user_id, seen):
        """Gather candidates from every strategy: item id -> strategy names."""
        ratings = self.user_ratings.get(user_id, {})
        lists = {}
        if ratings:
            lists["collaborative"] = self.generator.collaborative_candidates(
                user_id)
        if any(rating >= 4 for rating in ratings.values()):
            lists["content-based"] = self.generator.content_based_candidates(
                user_id)
        stated = sorted(self.declared.get(user_id, set()))
        lists["skill-based"] = [
            content.id
            for content in self.content_skills.get_content_by_skills(stated)]
        lists["popular"] = self.generator.popularity_candidates()

        sources = {}
        for source, item_ids in lists.items():
            for item_id in item_ids:
                if item_id not in seen:
                    sources.setdefault(item_id, []).append(source)
        return sources

    def _profile(self, user_id):
        """Skills the user stated plus skills of content they liked."""
        profile = set(self.declared.get(user_id, set()))
        for item_id, rating in self.user_ratings.get(user_id, {}).items():
            if rating >= 4:
                profile |= self.items[item_id]["tags"]
        return profile

    def _explain(self, source_names):
        """Build a plain-English reason from the strategies that agreed."""
        phrases = [SOURCE_REASONS[name] for name in source_names]
        if len(phrases) == 1:
            text = phrases[0]
        else:
            text = ", ".join(phrases[:-1]) + " and " + phrases[-1]
        return "Recommended because " + text + "."

    # ----- caching and feedback -----

    def get_recommendations(self, user_id, limit=5):
        """Return the top recommendations for a user, using the cache."""
        key = (user_id, limit)
        if key in self.cache:
            self.cache_hits += 1
            return list(self.cache[key])
        self.cache_misses += 1
        results = self._compute_recommendations(user_id, limit)
        self.cache[key] = results
        return list(results)

    def record_feedback(self, user_id, content_id, type, rating=None):
        """Save feedback, then refresh the data so new results reflect it."""
        if self.users.get(user_id) is None:
            raise UserNotFoundError("user %s not found" % user_id)
        if self.contents.get(content_id) is None:
            raise ContentNotFoundError("content %s not found" % content_id)

        self.interactions.record(user_id, content_id, type, rating)
        self.load_data()          # rebuild the dictionaries from the database
        self.cache.clear()        # old answers may now be out of date

    def cache_stats(self):
        """Return how well the cache is working."""
        requests = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / requests if requests else 0.0
        return {"hits": self.cache_hits, "misses": self.cache_misses,
                "size": len(self.cache), "hit_rate": round(hit_rate, 4)}
