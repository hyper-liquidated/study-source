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

# === Try to resolve DOI from Crossref ===
def crossref_doi_from_title(title: str) -> str:
    url = "https://api.crossref.org/works"
    try:
        r = requests.get(url, params={"query.title": title, "rows": 1})
        r.raise_for_status()
        items = r.json()["message"].get("items", [])
        if not items:
            return None
        cr_title = items[0].get("title", [""])[0]
        similarity = SequenceMatcher(None, title.lower(), cr_title.lower()).ratio()
        if similarity >= 0.85:
            doi = items[0].get("DOI")
            if doi:
                return f"https://doi.org/{doi}"
    except Exception:
        pass
    return None

# === Main GPT prompt ===
PROMPT = """
You are an expert research curator creating SIX DAILY FEEDS.

TRACK 1 – “The Social Layer” (cross-disciplinary behavioral, civic, and urban systems studies)
  • Examples: behavioral economics (scarcity mindset, choice overload, nudges);
    psychology & urban mental-health (noise, green space); civic tech & voter nudges;
    inequality / inheritance mobility; algorithmic governance.
  • Includes studies of urban complexity and adaptive infrastructure, such as real-time transit optimization,
    participatory sensor networks, emergent traffic modeling, modular housing, and city-scale simulations.
  • Feel free to include fresh adjacent topics (climate policy, AI ethics, education).
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
  • Include other adjacent institutional-finance angles (asset management, PE, liquidity).
  • Exactly 5 entries.

TRACK 3 – “Systems of Play” (game environments, simulation-based research, and interactive design)
  • Focus: game design, emergent systems, economic modeling in games, feedback loops, gamification of learning.
  • Examples: behavioral experiments in game environments, economic decision-making in simulated worlds,
    learning and attention models in gamified contexts, multiplayer strategy as coordination platforms.
  • Please include **at least one paper per batch involving League of Legends** (e.g. skill rating, coordination, feedback loops, game economy).
  • Favor studies that involve real-world systems emulated in games (e.g. marketplaces, politics, economies).
  • Bonus fields: mechanic, insight_type, game_context
  • Exactly 2 entries.

TRACK 4 – “The Health Layer” (physical, cognitive, and health interventions)
  • Focus: healthspan, biological adaptation, cognitive resilience, exercise and recovery effects, stress, sleep, sauna, cold exposure, light therapy, neuroendocrine function.
  • Includes: effect of weight training on memory, 3x/day micro workouts, sauna on cardiovascular biomarkers, dietary modulation of neuroinflammation, exercise-enhanced neuroplasticity.
  • Pulls from physiology, lifestyle intervention, clinical recovery, health optimization, and behavioral health fields.
  • Bonus fields: modality, population, mechanism
  • Exactly 2 entries.

TRACK 5 – “Long Horizons” (risk, governance, foresight, civilization-level systems)
  • Focus: existential risk, AI alignment, institutional foresight, space governance, biosecurity, post-scarcity governance.
  • Emphasize studies exploring scenario modeling, collapse and resilience dynamics, and long-term decision theory.
  • Favor speculative design and long-horizon simulation (e.g. agent-based future modeling, planetary-scale policy sims).
  • Game-based governance experiments may also be included if forward-looking or institutional in scope.
  • Exactly 2 entries.

TRACK 6 – “The State Layer” (comparative politics, governance systems, electoral policy, institutional trust)
  • Focus: democratic design, misinformation systems, global political behavior, cross-national policy evaluation, digital participation, and bipartisan institutional mechanisms.
  • Avoid partisan or editorial tone. Favor cross-validated, system-level studies from think tanks, academic journals, and public policy labs.
  • May include studies published by ideologically leaning institutions (e.g. Brookings, AEI) with an added "Counterpoint" field summarizing credible critiques from the opposite perspective.
  • Exactly 2 entries. Either:
    – one left and one right
    – or both neutral
  You must not include two left or two right in the same batch.

FOR EACH ENTRY return a JSON object with:
  track, title, authors, source, summary, why_notable

Also include:
• For Track 2: example, why_powerful, further_explanation, projects (2–3 real projects)
• For Track 3: mechanic, insight_type, game_context
• For Track 4: modality, population, mechanism
• For Track 6: lean, counterpoint

Return ONLY a JSON array of all 18 entries (no markdown, no extra text).
"""

# === Run ChatGPT ===
def generate():
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": PROMPT}]
    )
    return response.choices[0].message.content.strip()

# === Main ===
def main():
    raw = generate()
    try:
        studies = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError("GPT output was not valid JSON:\n" + raw)

    for s in studies:
        url = s.get("source_url", "")
        if url and url.startswith("http"):
            continue
        doi_url = crossref_doi_from_title(s["title"])
        if doi_url:
            s["source_url"] = doi_url
        else:
            query = urllib.parse.quote_plus(s["title"])
            s["source_url"] = f"https://scholar.google.com/scholar?q={query}"

    os.makedirs("data", exist_ok=True)
    with open("data/studies.json", "w", encoding="utf-8") as f:
        json.dump(studies, f, indent=2)
    print(f"[INFO] Wrote {len(studies)} studies to data/studies.json")

if __name__ == "__main__":
    main()
