from enum import Enum


# alchemist's role constants
ALCHEMIST_ROLE = "Alchemists"

# master's role constants
MASTER_ROLE_POINTS_THRESHOLD = 50_000
MASTER_ROLE = "Master Alchemist"

# valiant's role constants
VALIANT_ROLE_POINTS_THRESHOLD = 3_000
VALIANT_ROLE = "Valiant Alchemist"

# apprentice's role constants
APPRENTICE_ROLE = "Apprentice Alchemists"
APPRENTICE_ROLE_POINTS_THRESHOLD = 0


# Google Sheets constants
USERNAME_COLUMN = "Discord handle"
POINTS_COLUMN = "Total CQT"


# notification types
class NotificationTypes(str, Enum):
    GREET_MASTER = "greet_master"
    GREET_VALIANT = "greet_valiant"
    GREET_APPRENTICE = "greet_apprentice"
