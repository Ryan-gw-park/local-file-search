import sys
import os
import traceback
import logging
from datetime import datetime

# Setup crash logging
LOG_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(LOG_DIR, "..", "crash_log.txt")

# Configure logging to both file and console
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def exception_hook(exc_type, exc_value, exc_traceback):
    """Global exception handler that logs crashes to file."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logger.critical(f"UNHANDLED EXCEPTION:\n{error_msg}")
    
    # Also write to a separate crash file with timestamp
    crash_file = os.path.join(LOG_DIR, "..", f"crash_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    with open(crash_file, 'w', encoding='utf-8') as f:
        f.write(f"Crash Time: {datetime.now().isoformat()}\n")
        f.write(f"Exception Type: {exc_type.__name__}\n")
        f.write(f"Exception Value: {exc_value}\n")
        f.write(f"\nFull Traceback:\n{error_msg}")
    
    print(f"\n\n{'='*60}")
    print(f"CRASH DETECTED! Log saved to: {crash_file}")
    print(f"{'='*60}\n")

# Install exception hook
sys.excepthook = exception_hook

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info(f"Application starting at {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    try:
        from ui import main
        main()
    except Exception as e:
        logger.critical(f"Fatal error in main: {e}")
        logger.critical(traceback.format_exc())
        raise
    finally:
        logger.info(f"Application exiting at {datetime.now().isoformat()}")
