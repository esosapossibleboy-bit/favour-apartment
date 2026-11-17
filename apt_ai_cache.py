import re
import time
from apt_security import APARTMENT_LISTING

class FastSlotCache:
    """Level 7 Superpower: Ultra-fast RAM cache for booked slots with instant invalidation."""
    def __init__(self, ttl_seconds: int = 30):
        self.ttl = ttl_seconds
        self._store: dict[str, tuple[float, list[str]]] = {}

    def get(self, key: str) -> list[str] | None:
        if key in self._store:
            expires_at, slots = self._store[key]
            if time.time() < expires_at:
                return slots
            del self._store[key]
        return None

    def set(self, key: str, slots: list[str]):
        self._store[key] = (time.time() + self.ttl, slots)

    def invalidate(self, key: str):
        self._store.pop(key, None)

    def clear(self):
        self._store.clear()

SLOT_CACHE = FastSlotCache(ttl_seconds=30)

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+(rules|instructions)",
    r"reveal\s+(the\s+)?(host\s+)?passcode",
    r"system\s+prompt",
    r"dump\s+(all\s+)?(database|users|nin|bvn)",
]

def ask_tenant_ai(question: str) -> dict:
    """Level 9 Superpower: Grounded RAG + Guardrail AI Assistant for Favour Apartment."""
    q = (question or "").strip()
    if len(q) < 3:
        return {"blocked": False, "answer": "Please type a question about rent, rooms, location, or security."}

    if any(re.search(pat, q.lower()) for pat in INJECTION_PATTERNS):
        return {"blocked": True, "answer": "🛡️ Blocked by AI Security Guardrail: Unsafe instruction detected."}

    knowledge_cards = [
        f"Annual rent for {APARTMENT_LISTING['title']} is {APARTMENT_LISTING['rent_annual']}, payable after physical inspection.",
        "We have 3 modern self-contained units (Unit 1, Unit 2, and Unit 3). Each unit has 1 bedroom, a sitting room, kitchen, bathroom, and toilet.",
        f"{APARTMENT_LISTING['title']} is located in {APARTMENT_LISTING['area']}. The exact street address unlocks automatically once your tour is confirmed.",
        "For resident safety, every visitor must verify a real Nigerian phone number, current address, and an 11-digit NIN or BVN (encrypted & masked). Maximum 2 visitors per tour.",
        "Daytime inspection slots run at 10:00 AM, 12:00 PM, 02:30 PM, and 04:30 PM, booked 1 to 30 days ahead. Present your 4-digit Gate PIN and ID at the gate.",
        f"You can reach the host directly at {APARTMENT_LISTING['host_phone']} or save your pass on WhatsApp after booking.",
    ]

    q_words = {w.lower() for w in re.findall(r"[a-z0-9]+", q) if len(w) > 2}
    best_score = 0
    best_card = None
    for card in knowledge_cards:
        c_words = {w.lower() for w in re.findall(r"[a-z0-9]+", card) if len(w) > 2}
        score = len(q_words & c_words)
        if score > best_score:
            best_score = score
            best_card = card

    if not best_card:
        return {
            "blocked": False,
            "answer": f"I don't have that specific detail yet. Please call or WhatsApp the host at {APARTMENT_LISTING['host_phone']}.",
        }
    return {"blocked": False, "answer": best_card}
