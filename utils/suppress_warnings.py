# utils/suppress_warnings.py
import warnings
from urllib3.exceptions import NotOpenSSLWarning

# Standard warning filter (for redundancy — harmless if used with override)
warnings.filterwarnings("ignore", category=NotOpenSSLWarning)

# Override handler to catch early-emitted warning
def block_notopenssl(message, category, *args, **kwargs):
    # Suppress only NotOpenSSLWarning
    if "NotOpenSSLWarning" in str(category):
        return  # Do nothing
    return warnings._original_showwarning(message, category, *args, **kwargs)

# Apply override
warnings._original_showwarning = warnings.showwarning
warnings.showwarning = block_notopenssl