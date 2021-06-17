from enum import Enum


# alchemist's role constants
ALCHEMIST_ROLE = "Alchemists"

# master's role constants
MASTER_ROLE_ID = 2
MASTER_ROLE = "Master Alchemist"

# valiant's role constants
VALIANT_ROLE_ID = 3
VALIANT_ROLE = "Valiant Alchemist"

# apprentice's role constants
APPRENTICE_ROLE_ID = 4
APPRENTICE_ROLE = "Apprentice Alchemists"


# notification types
class NotificationTypes(str, Enum):
    GREET_MASTER = "greet_master"
    GREET_VALIANT = "greet_valiant"
    GREET_APPRENTICE = "greet_apprentice"


WELCOME_REACTION = "\U0001f973"  # :partying_face:
