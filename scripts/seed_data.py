"""Fill the database with the sample dataset.

Run it from the project folder:  python -m scripts.seed_data
"""
from data.database import get_session, init_db
from data.repositories import (ContentRepository, ContentSkillRepository,
                               InteractionRepository, SkillRepository,
                               UserRepository, UserSkillRepository)
from tests.test_data import CONTENT, INTERACTIONS, USERS


def seed(session, interactions_data=None):
    """Load the sample data. Returns False if users already exist."""
    users = UserRepository(session)
    if users.get_all():
        return False

    skills = SkillRepository(session)
    content = ContentRepository(session)
    user_skills = UserSkillRepository(session)
    content_skills = ContentSkillRepository(session)
    interactions = InteractionRepository(session)

    # Users and the skills they have (inserted in order, so ids start at 1)
    for name, interests, skill_levels in USERS:
        user = users.create(name, interests)
        for skill_name, level in skill_levels.items():
            skill = skills.get_or_create(skill_name)
            user_skills.set_skill(user.id, skill.id, level)

    # Content and the skills it teaches
    for title, category, difficulty, popularity, skill_names in CONTENT:
        item = content.create(title, category, difficulty, popularity)
        for skill_name in skill_names:
            skill = skills.get_or_create(skill_name)
            content_skills.link(item.id, skill.id)
    rows = INTERACTIONS if interactions_data is None else interactions_data

    # What users did with the content
    for user_id, content_id, kind, rating in rows:
        interactions.record(user_id, content_id, kind, rating)

    return True


def main():
    """Create the tables if needed, then seed them."""
    init_db()
    session = get_session()
    try:
        if seed(session):
            print("Database seeded:",
                  len(UserRepository(session).get_all()), "users,",
                  len(ContentRepository(session).get_all()), "content items,",
                  len(SkillRepository(session).get_all()), "skills,",
                  len(InteractionRepository(session).get_all()),
                  "interactions")
        else:
            print("Database already has data - nothing to do.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
