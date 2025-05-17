#!/usr/bin/env python3
"""
fetch_studies.py

Uses GPT-4o to generate studies across six tracks with robust prompts.
Fills in missing source URLs via Crossref or Google Scholar fallback.
Writes output to data/studies.json
"""
import os
import json
import requests
import urllib.parse
from difflib import SequenceMatcher
import openai

# === Load OpenAI key ===
oai_key = os.getenv("OPENAI_API_KEY")
if not oai_key:
    raise ValueError("Missing OPENAI_API_KEY environment variable")
openai.api_key = oai_key

# === 1. Helper to resolve a DOI via Crossref by title ===
def crossref_doi_from_title(title: str) -> str:
    url = "https://api.crossref.org/works"
    try:
        resp = requests.get(url, params={"query.title": title, "rows": 1})
        resp.raise_for_status()
        items = resp.json().get("message", {}).get("items", [])
        if not items:
            return None
        cr_title = items[0].get("title", [""])[0]
        sim = SequenceMatcher(None, title.lower(), cr_title.lower()).ratio()
        if sim >= 0.85:
            doi = items[0].get("DOI")
            if doi:
                return f"https://doi.org/{doi}"
    except Exception:
        pass
    return None

# === 2. The full six-track curator prompt ===
PROMPT = """
You are an expert research curator creating SIX DAILY FEEDS.

TRACK 1 – “The Social Layer” (cross-disciplinary behavioral, civic, and urban systems studies)
  • Examples: behavioral economics (scarcity mindset, choice overload, nudges);
    psychology & urban mental-health (noise, green space); civic tech & voter nudges;
    inequality / inheritance mobility; algorithmic governance.
  • Includes studies of urban complexity and adaptive infrastructure, such as real-time transit optimization,
    participatory sensor networks, emergent traffic modeling, modular housing, and city-scale simulations.
  • Exactly 5 entries.

TRACK 2 – “Architectures of Capital” (crypto & finance infrastructure)
  • Examples: Zero-knowledge proofs & recursive SNARKs
      – Rollups & data availability / modular L2s
      – DeFi systemic risk (collateral rehypothecation, leverage chains)
      – Stablecoin peg & run dynamics
      – Latency arbitrage & market microstructure
      – Tokenized Real-World Assets (RWA) & on-chain treasuries
      – Staking & Restaking economics (EigenLayer, LSTs)
      – MEV & proposer-builder separation, auction design
      – Cross-chain bridges & interoperability (IBC, LayerZero)
      – Scalability & new execution layers (parallel EVMs, zk-VMs)
      – Derivatives & structured products (options AMMs, perps 2.0)
      – Stablecoin reserve attestations on-chain (Circle, Paxos)
      – Emerging middleware: intent-based protocols, shared sequencers
  • Include adjacent institutional-finance angles (asset management, PE, liquidity).
  • Exactly 5 entries.

TRACK 3 – “Systems of Play” (game environments, simulation-based research, and interactive design)
  • Focus: game design, emergent systems, economic modeling in games, feedback loops, gamification of learning.
  • Examples: behavioral experiments in game environments, economic decision-making in simulated worlds,
    learning and attention models in gamified contexts, multiplayer strategy as coordination platforms.
  • Please include at least one paper per batch involving League of Legends.
  • Bonus fields: mechanic, insight_type, game_context
  • Exactly 2 entries.

TRACK 4 – “The Health Layer” (physical, cognitive, and health interventions)
  • Focus: healthspan, biological adaptation, cognitive resilience, exercise and recovery effects, stress, sleep, sauna, cold exposure, light therapy, neuroendocrine function.
  • Examples: effect of weight training on memory, 3x/day micro workouts, sauna on cardiovascular biomarkers, dietary modulation of neuroinflammation, exercise-enhanced neuroplasticity.
  • Bonus fields: modality, population, mechanism
  • Exactly 2 entries.

TRACK 5 – “Long Horizons” (risk, governance, foresight, civilization-level systems)
  • Focus: existential risk, AI alignment, institutional foresight, space governance, biosecurity, post-scarcity governance.
  • Examples: agent-based modeling, collapse simulations, resilience dynamics.
  • Exactly 2 entries.

TRACK 6 – “The State Layer” (comparative politics, governance systems, electoral policy, institutional trust)
  • Focus: democratic design, misinformation systems, cross-national policy evaluation, digital participation, bipartisan mechanisms.
  • May include studies from ideologically-leaning institutions (Brookings, AEI) with a "counterpoint" critique.
  • Exactly 2 entries: one left + one right, or both neutral. Never two left or two right.
  • Bonus fields: lean, counterpoint

FOR EACH ENTRY return a JSON object with:
  track, title, authors, source, summary, why_notable

Also include:
• Track 2: example, why_powerful, further_explanation, projects (2–3 items)
• Track 3: mechanic, insight_type, game_context
• Track 4: modality, population, mechanism
• Track 6: lean, counterpoint

Return ONLY a JSON array of exactly 18 objects (no markdown, no extra text).
"""

# === 3. Call ChatGPT ===
def generate():
    resp = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": PROMPT}]
    )
    return resp.choices[0].message.content.strip()

# === 4. Main workflow ===
def main():
    raw = generate()
    try:
        studies = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError("GPT output was not valid JSON:\n" + raw)

    # Fill in source_url if missing
    for s in studies:
        if not s.get("source_url", "").startswith("http"):
            doi = crossref_doi_from_title(s["title"])
            if doi:
                s["source_url"] = doi
            else:
                query = urllib.parse.quote_plus(s["title"])
                s["source_url"] = f"https://scholar.google.com/scholar?q={query}"

    os.makedirs("data", exist_ok=True)
    with open("data/studies.json", "w", encoding="utf-8") as f:
        json.dump(studies, f, indent=2)

    print(f"[INFO] Wrote {len(studies)} studies to data/studies.json")

if __name__ == "__main__":
    main()