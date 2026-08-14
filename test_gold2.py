import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from gold_contact_engine import GoldContactEngine

engine = GoldContactEngine()
engine.seed = engine.seed[:3]
engine.run()
