"""Data access layer: one repository class per table.

A repository hides the database details. The rest of the project asks a
repository for data instead of writing database queries itself.
"""
from data.models import (Content, ContentSkill, Interaction, Skill, User,
                         UserSkill)

# The kinds of interaction we accept
INTERACTION_TYPES = ("view", "like", "complete", "rating")


class UserRepository:
    """Reads and writes rows in the users table."""

    def __init__(self, session):
        self.session = session

    def create(self, name, interests=""):
        """Add a new user and return it."""
        user = User(name=name, interests=interests)
        self.session.add(user)
        self.session.commit()
        return user

    def get(self, user_id):
        """Return the user with this id, or None if there is no such user."""
        return self.session.get(User, user_id)

    def get_all(self):
        """Return every user."""
        return self.session.query(User).all()


class SkillRepository:
    """Reads and writes rows in the skills table."""

    def __init__(self, session):
        self.session = session

    def get_or_create(self, name):
        """Return the skill with this name, creating it if needed."""
        # "Python " and "python" are the same skill
        name = name.strip().lower()
        skill = self.session.query(Skill).filter_by(name=name).first()
        if skill is None:
            skill = Skill(name=name)
            self.session.add(skill)
            self.session.commit()
        return skill

    def get_all(self):
        """Return every skill."""
        return self.session.query(Skill).all()


class ContentRepository:
    """Reads and writes rows in the content table."""

    def __init__(self, session):
        self.session = session

    def create(self, title, category="", difficulty=1, popularity=0.0):
        """Add a new piece of content and return it."""
        content = Content(title=title, category=category,
                          difficulty=difficulty, popularity=popularity)
        self.session.add(content)
        self.session.commit()
        return content

    def get(self, content_id):
        """Return the content with this id, or None if it does not exist."""
        return self.session.get(Content, content_id)

    def get_all(self):
        """Return all content."""
        return self.session.query(Content).all()


class UserSkillRepository:
    """Reads and writes rows in the user_skills table."""

    def __init__(self, session):
        self.session = session

    def set_skill(self, user_id, skill_id, proficiency=1):
        """Give a user a skill, or update the level if they already have it."""
        link = self.session.get(UserSkill, (user_id, skill_id))
        if link is None:
            link = UserSkill(user_id=user_id, skill_id=skill_id,
                             proficiency=proficiency)
            self.session.add(link)
        else:
            link.proficiency = proficiency
        self.session.commit()
        return link

    def get_for_user(self, user_id):
        """Return all skills a user has."""
        return self.session.query(UserSkill).filter_by(user_id=user_id).all()


class ContentSkillRepository:
    """Reads and writes rows in the content_skills table."""

    def __init__(self, session):
        self.session = session

    def link(self, content_id, skill_id):
        """Link content to a skill (does nothing if already linked)."""
        existing = self.session.get(ContentSkill, (content_id, skill_id))
        if existing is None:
            existing = ContentSkill(content_id=content_id, skill_id=skill_id)
            self.session.add(existing)
            self.session.commit()
        return existing

    def get_skill_ids(self, content_id):
        """Return the ids of the skills a piece of content teaches."""
        rows = self.session.query(ContentSkill).filter_by(
            content_id=content_id).all()
        return [row.skill_id for row in rows]

    def get_content_by_skills(self, skill_names):
        """Return content that teaches at least one of the given skills."""
        names = [name.strip().lower() for name in skill_names]
        if not names:
            return []
        return (self.session.query(Content)
                .join(ContentSkill, ContentSkill.content_id == Content.id)
                .join(Skill, Skill.id == ContentSkill.skill_id)
                .filter(Skill.name.in_(names))
                .distinct()
                .order_by(Content.id)
                .all())


class InteractionRepository:
    """Reads and writes rows in the interactions table."""

    def __init__(self, session):
        self.session = session

    def record(self, user_id, content_id, type, rating=None):
        """Save something a user did with a piece of content."""
        if type not in INTERACTION_TYPES:
            raise ValueError("type must be one of: " +
                             ", ".join(INTERACTION_TYPES))
        if rating is not None and not 1 <= rating <= 5:
            raise ValueError("rating must be between 1 and 5")
        interaction = Interaction(user_id=user_id, content_id=content_id,
                                  type=type, rating=rating)
        self.session.add(interaction)
        self.session.commit()
        return interaction

    def get_user_history(self, user_id):
        """Return everything a user has done, oldest first."""
        return (self.session.query(Interaction)
                .filter_by(user_id=user_id)
                .order_by(Interaction.id)
                .all())

    def get_all(self):
        """Return every interaction."""
        return self.session.query(Interaction).all()
