"""Sample dataset (12 users, 24 content items) for seeding and testing.

IDs are positions that start at 1: the first user is user 1, the first
content item is content 1, and so on. A fresh database gets the same ids.
"""

# (name, interests, {skill: proficiency from 1 to 5})
USERS = [
    ("Asha", "data science,python", {"python": 3, "statistics": 2}),
    ("Ben", "data science,machine learning",
     {"python": 4, "machine learning": 2}),
    ("Chitra", "data science,sql", {"sql": 3, "python": 2}),
    ("Dev", "web development,javascript",
     {"javascript": 3, "html": 4, "css": 3}),
    ("Esha", "web development,react", {"javascript": 4, "react": 2, "css": 3}),
    ("Farhan", "web development,apis", {"javascript": 3, "apis": 2}),
    ("Gita", "databases,sql", {"sql": 4}),
    ("Hari", "devops,docker", {"docker": 2, "git": 3, "linux": 2}),
    ("Isha", "python,apis", {"python": 4, "apis": 3}),
    ("Jai", "data science,statistics", {"statistics": 4, "python": 3}),
    ("Kavya", "web development,design", {"html": 3, "css": 4}),
    ("Lia", "python", {}),   # new user with no history: tests cold start
]

# (title, category, difficulty 1-3, popularity 0-1, [skills taught])
CONTENT = [
    ("Python for Beginners", "programming", 1, 0.95, ["python"]),
    ("Data Analysis with Pandas", "data science", 2, 0.85,
     ["python", "pandas"]),
    ("Statistics Fundamentals", "data science", 1, 0.70, ["statistics"]),
    ("Intro to Machine Learning", "data science", 2, 0.90,
     ["python", "machine learning", "statistics"]),
    ("Advanced Machine Learning", "data science", 3, 0.60,
     ["python", "machine learning"]),
    ("Data Visualization with Python", "data science", 2, 0.65,
     ["python", "pandas"]),
    ("SQL Basics", "databases", 1, 0.90, ["sql"]),
    ("Advanced SQL Queries", "databases", 3, 0.55, ["sql"]),
    ("Database Design", "databases", 2, 0.50, ["sql"]),
    ("SQL for Data Analysis", "databases", 2, 0.75, ["sql", "pandas"]),
    ("HTML and CSS Basics", "web development", 1, 0.88, ["html", "css"]),
    ("JavaScript Essentials", "web development", 1, 0.92, ["javascript"]),
    ("Modern CSS Layouts", "web development", 2, 0.55, ["css"]),
    ("React for Beginners", "web development", 2, 0.80,
     ["react", "javascript"]),
    ("Advanced React Patterns", "web development", 3, 0.45,
     ["react", "javascript"]),
    ("Building REST APIs", "backend", 2, 0.70, ["apis", "python"]),
    ("Web APIs with JavaScript", "web development", 2, 0.60,
     ["apis", "javascript"]),
    ("Git and GitHub Basics", "tools", 1, 0.85, ["git"]),
    ("Docker for Beginners", "devops", 2, 0.75, ["docker"]),
    ("Docker in Production", "devops", 3, 0.40, ["docker", "git"]),
    ("Linux Command Line", "tools", 1, 0.65, ["linux"]),
    ("CI/CD Pipelines", "devops", 3, 0.35, ["docker", "git"]),
    ("Deploying Web Apps", "devops", 2, 0.50, ["docker", "apis"]),
    ("Deep Learning Basics", "data science", 3, 0.70,
     ["machine learning", "python"]),
]

# (user id, content id, type, rating); rating is only used for "rating"
INTERACTIONS = [
    # Asha
    (1, 1, "like", None), (1, 2, "rating", 5), (1, 3, "rating", 4),
    (1, 4, "rating", 4), (1, 6, "rating", 5), (1, 5, "view", None),
    # Ben
    (2, 1, "rating", 4), (2, 2, "rating", 4), (2, 4, "rating", 5),
    (2, 5, "rating", 5), (2, 24, "rating", 5), (2, 3, "view", None),
    # Chitra
    (3, 7, "rating", 5), (3, 10, "like", None), (3, 2, "rating", 4),
    (3, 1, "rating", 4), (3, 9, "rating", 3), (3, 8, "rating", 4),
    # Dev
    (4, 11, "rating", 5), (4, 12, "complete", None), (4, 13, "rating", 4),
    (4, 14, "rating", 4), (4, 17, "rating", 3), (4, 18, "rating", 4),
    # Esha
    (5, 12, "rating", 5), (5, 14, "complete", None), (5, 15, "rating", 4),
    (5, 11, "rating", 4), (5, 13, "rating", 5), (5, 17, "rating", 4),
    # Farhan
    (6, 12, "rating", 4), (6, 17, "rating", 5), (6, 16, "rating", 4),
    (6, 14, "rating", 3), (6, 18, "rating", 4), (6, 23, "view", None),
    # Gita
    (7, 7, "rating", 5), (7, 8, "rating", 5), (7, 9, "like", None),
    (7, 10, "rating", 4), (7, 3, "view", None),
    # Hari
    (8, 18, "rating", 5), (8, 19, "complete", None), (8, 21, "rating", 5),
    (8, 20, "rating", 4), (8, 22, "rating", 4), (8, 23, "rating", 4),
    # Isha
    (9, 1, "rating", 5), (9, 16, "complete", None), (9, 2, "rating", 4),
    (9, 17, "view", None), (9, 18, "rating", 4), (9, 19, "rating", 3),
    # Jai
    (10, 3, "rating", 5), (10, 4, "like", None), (10, 1, "rating", 4),
    (10, 2, "rating", 4), (10, 24, "rating", 4), (10, 6, "rating", 4),
    # Kavya
    (11, 11, "rating", 5), (11, 13, "rating", 5), (11, 12, "rating", 4),
    (11, 14, "view", None), (11, 18, "rating", 3),
    # Lia (user 12) has no interactions on purpose
]
