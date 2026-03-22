# Package initialization file
from .utils.database import (
    get_db_connection,
    init_db,
    get_journal_stats,
    get_meditation_stats
)

__version__ = '1.0.0'
