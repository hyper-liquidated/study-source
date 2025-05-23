#!/usr/bin/env python3
import os
import json
import openai
import psycopg2
from difflib import SequenceMatcher
import requests

# 1) Tell Python how to talk to OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# 2) This function asks OpenAI for your six tracks of studies
def fetch_studies():
    prompt = "YOUR SIX-TRACK PROMPT HERE"
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": prompt}]
    )
    text = response.choices[0].message.content.strip("```")
    studies = json.loads(text)
    # (You still have your DOI/URL lookup logic here if you want)
    return studies

# 3) This function puts each study into your Supabase database
def save_to_db(studies):
    db_url = os.getenv("DATABASE_URL")
    conn = psycopg2.connect(db_url)     # Connect to Supabase
    cur = conn.cursor()

    sql = """
    INSERT INTO studies
      (track, title, authors, source, summary, why_notable, doi, source_url, year, extra)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (doi) DO NOTHING;
    """

    for s in studies:
        cur.execute(sql, (
            s.get("track"),
            s.get("title"),
            ", ".join(s.get("authors", [])),
            s.get("source"),
            s.get("summary"),
            s.get("why_notable"),
            s.get("doi"),
            s.get("source_url"),
            s.get("year"),
            json.dumps({k: v for k, v in s.items() if k not in {
                "track","title","authors","source","summary","why_notable","doi","source_url","year"
            }})
        ))

    conn.commit()
    cur.close()
    conn.close()
    print(f"Saved {len(studies)} studies.")

# 4) Run both functions when you call this script
if __name__ == "__main__":
    studies = fetch_studies()
    # (Optional) still write to JSON file:
    with open("data/studies.json", "w") as f:
        json.dump(studies, f, indent=2)

    save_to_db(studies)
