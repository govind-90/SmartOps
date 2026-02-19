"""Wrapper module to load views/03_Analytics.py using a valid module name."""
from pathlib import Path
import importlib.util

_file = Path(__file__).parent / "03_Analytics.py"
spec = importlib.util.spec_from_file_location("views._03_Analytics", str(_file))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
