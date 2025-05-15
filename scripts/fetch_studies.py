import os, json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

prompt = """
Give me 5 recent behavioral-science studies and 5 recent crypto/finance studies.
Output JSON array of objects with keys:
  title, authors, source, summary, notable
"""

resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role":"user","content": prompt}],
    temperature=0.7
)

studies = json.loads(resp.choices[0].message.content)
os.makedirs("data", exist_ok=True)
with open("data/studies.json","w") as f:
    json.dump(studies, f, indent=2)
print(f"Wrote {len(studies)} studies to data/studies.json")
