#!/usr/bin/env python
"""Import the tab-separated Freshers Party schedule from abc.txt."""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Event


TIME_RANGE = re.compile(r"^(.+?)\s+to\s+(.+?)$", re.IGNORECASE)


def parse_time(value: str, date_text: str, year: int | None):
    if year is None:
        return None
    value = value.strip().lower().replace(" ", "")
    for fmt in ("%I:%M%p", "%I%p"):
        try:
            parsed = datetime.strptime(value, fmt)
            normalized_date = date_text.lower().replace("sept", "sep")
            date = datetime.strptime(f"{normalized_date}-{year}", "%d-%b-%Y")
            return date.replace(hour=parsed.hour, minute=parsed.minute)
        except ValueError:
            continue
    return None


def parse_schedule(schedule_path: str, year: int | None = None) -> list[dict]:
    rows = []
    with open(schedule_path, "r", encoding="utf-8") as schedule_file:
        for line in schedule_file:
            columns = [column.strip() for column in line.rstrip("\n").split("\t")]
            if len(columns) < 4 or columns[0].lower() == "day":
                continue
            day, date_text, name, time_text = columns[:4]
            time_match = TIME_RANGE.match(time_text)
            start_time = end_time = None
            if time_match:
                start_time = parse_time(time_match.group(1), date_text, year)
                end_time = parse_time(time_match.group(2), date_text, year)
            rows.append({
                "day": day,
                "date_text": date_text,
                "name": name,
                "start_time": start_time,
                "end_time": end_time,
            })
    return rows


def import_schedule(schedule_path: str, year: int | None = None, session_factory=SessionLocal):
    created = updated = skipped = 0
    db = session_factory()
    try:
        for row in parse_schedule(schedule_path, year):
            event = db.query(Event).filter(Event.name == row["name"]).first()
            values = {
                "description": f"{row['day']}, {row['date_text']}",
                "start_time": row["start_time"],
                "end_time": row["end_time"],
            }
            if event:
                changed = any(getattr(event, key) != value for key, value in values.items())
                if changed:
                    for key, value in values.items():
                        setattr(event, key, value)
                    updated += 1
                else:
                    skipped += 1
            else:
                db.add(Event(name=row["name"], **values))
                created += 1
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    print("\n" + "=" * 60)
    print("Schedule Import Summary")
    print("=" * 60)
    print(f"Created:               {created}")
    print(f"Updated:               {updated}")
    print(f"Skipped (unchanged):   {skipped}")
    print("Competitions detected: 0")
    print(f"Plain schedule rows:   {len(parse_schedule(schedule_path, year))}")
    print("=" * 60 + "\n")
    return created, updated, skipped


def main():
    parser = argparse.ArgumentParser(description="Import the Freshers Party schedule.")
    parser.add_argument("schedule_path")
    parser.add_argument("--year", type=int, default=None, help="Year for date/time fields")
    args = parser.parse_args()
    import_schedule(args.schedule_path, args.year)


if __name__ == "__main__":
    main()