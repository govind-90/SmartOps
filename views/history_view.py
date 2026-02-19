"""Wrapper module to load views/04_History.py using a valid module name."""
from pathlib import Path
import importlib.util

_file = Path(__file__).parent / "04_History.py"
spec = importlib.util.spec_from_file_location("views._04_History", str(_file))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
