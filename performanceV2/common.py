from typing import List, Set, Tuple

# --- Constants ---

IMPORT_USERS = [
    'FADWA.ERRAZIKI', 'AYOUB.SOURISTE', 'AYMANE.BERRIOUA', 'SANA.IDRISSI', 'AMINA.SAISS',
    'KHADIJA.OUFKIR', 'ZOHRA.HMOUDOU', 'SIMO.ONSI', 'YOUSSEF.ASSABIR', 'ABOULHASSAN.AMINA',
    'MEHDI.OUAZIR', 'OUMAIMA.EL.OUTMANI', 'HAMZA.ALLALI', 'MUSTAPHA.BOUJALA', 'HIND.EZZAOUI',
    'MOHAMED.BOUIDAR', 'HOUDA.EZZAOUI', 'YAHYA.ANEJARN'
]

EXPORT_USERS = [
    'IKRAM.OULHIANE', 'MOURAD.ELBAHAZ', 'MOHSINE.SABIL', 'AYA.HANNI',
    'ZAHIRA.OUHADDA', 'CHAIMAAE.EJJARI', 'HAFIDA.BOOHADDOU', 'KHADIJA.HICHAMI', 'FATIMA.ZAHRA.BOUGSIM'
]

# Combined list of all target users for reports
TARGET_USERS = IMPORT_USERS + EXPORT_USERS

MANUAL_STATUSES = {"COPIED", "COPY", "NEW"}

# --- Helper Functions ---

def classify_file_activity(global_history: List[str], user_history: List[str] = None) -> Tuple[bool, bool]:
    """
    Determines if a file activity is 'Automatic' or 'Manual'.
    
    Logic:
    - Automatic: If 'INTERFACE' is present in the GLOBAL history status.
    - Manual: If any of MANUAL_STATUSES are present in the USER history status (or global if not provided) AND it is NOT Automatic.
    
    Args:
        global_history: Full history of the declaration (e.g. all users' actions).
        user_history: Specific history of the user being analyzed. If None, defaults to global_history.
    
    Returns:
        A tuple (is_manual, is_automatic)
    """
    
    # Ensure inputs are sets for faster lookup
    global_set = set(global_history)
    user_set = set(user_history) if user_history is not None else global_set
    
    is_automatic = 'INTERFACE' in global_set
    
    # Check intersection with manual statuses in the specific scope (User or Global)
    has_manual_trigger = bool(MANUAL_STATUSES.intersection(user_set))
    
    # Precise definition: Manual only if triggered manually AND not an interface file
    is_manual = has_manual_trigger and not is_automatic
    
    return is_manual, is_automatic
