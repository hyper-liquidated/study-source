#!/usr/bin/env python3
"""
Generate 10 daily studies (5 Social-Layer + 5 Architectures-of-Capital)
and write them to data/studies.json for downstream rendering.
"""

import os, json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PROMPT = """
You are an expert research curator creating TWO DAILY FEEDS.

TRACK 1 – “The Social Layer” (cross-disciplinary behavioral & policy studies)
  • Examples: behavioral economics (scarcity mindset, choice overload, nudges);
    psychology & urban mental-health (noise, green space); civic tech & voter nudges;
    inequality / inheritance mobility; algorithmic governance.
  • Feel free to include fresh adjacent topics (climate policy, AI ethics, education).
  • Exactly 5 entries.

TRACK 2 – “Architectures of Capital” (crypto & finance infrastructure)
  • Examples (you may choose from or related to):
      – Zero-knowledge proofs & recursive SNARKs
      – Rollups & data availability / modular L2s
      – DeFi systemic risk (collateral rehypothecation, leverage chains)
      – Stablecoin peg & run dynamics
      – Latency arbitrage & market microstructure
      – **Tokenized Real-World Assets (RWA) & on-chain treasuries**
      – **Staking & Restaking economics (EigenLayer, LSTs)**
      – **MEV & proposer-builder separation, auction design**
      – **Cross-chain bridges & interoperability (IBC, LayerZero)**
      – **Scalability & new execution layers (parallel EVMs, zk-VMs)**
      – **Derivatives & structured products (options AMMs, perps 2.0)**
      – **Stablecoin reserve attestations on-chain (Circle, Paxos)**
      – **Emerging middleware: intent-based protocols, shared sequencers**
  • Include other adjacent institutional-finance angles (asset management, PE, liquidity).
  • Exactly 5 entries.

FOR EACH ENTRY output a JSON object with:
  title, authors, source, summary, why_notable, tags
  (tags must be one of: "interested", "maybe later", "not now")

FOR TRACK 2 ALSO include:
  example, why_powerful, further_explanation, projects (array of 2-3 real projects)

Return ONLY a JSON array of 10 objects (no markdown, no extra text).
"""

def main() -> None:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": PROMPT}],
        temperature=0.7,
    )

    studies = json.loads(resp.choices[0].message.content)

    os.makedirs("data", exist_ok=True)
    with open("data/studies.json", "w", encoding="utf-8") as f:
        json.dump(studies, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(studies)} studies to data/studies.json")

if __name__ == "__main__":
    main()
