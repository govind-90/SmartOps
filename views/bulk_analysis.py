"""Wrapper module to load views/02_Bulk_Analysis.py using a valid module name."""
from pathlib import Path
import importlib.util

_file = Path(__file__).parent / "02_Bulk_Analysis.py"
spec = importlib.util.spec_from_file_location("views._02_Bulk_Analysis", str(_file))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
