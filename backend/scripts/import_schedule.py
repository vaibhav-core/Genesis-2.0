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


ROW_PATTERN = re.compile(
    r"^\s*(?P<day>\w+)\s+(?P<date>\d{1,2}-\w+)\s+(?P<name>.*?)\s+"
    r"(?P<start>\d{1,2}:?\d{0,2}\s*(?:am|pm))\s+to\s+"
    r"(?P<end>\d{1,2}:?\d{0,2}\s*(?:am|pm))\s*$",
    re.IGNORECASE,
)


class ScheduleParseError(ValueError):
    """Raised when a non-empty schedule row cannot be parsed safely."""


def parse_time(value: str, date_text: str, year: int | None):
    value = value.strip().lower().replace(" ", "")
    for fmt in ("%I:%M%p", "%I%p"):
        try:
            parsed = datetime.strptime(value, fmt)
            normalized_date = date_text.lower().replace("sept", "sep")
            date = datetime.strptime(f"{normalized_date}-{year}", "%d-%b-%Y")
            return date.replace(hour=parsed.hour, minute=parsed.minute)
        except ValueError:
            continue
    raise ScheduleParseError(f"Invalid time/date: {date_text} {value}")


def parse_schedule(schedule_path: str, year: int | None = None) -> list[dict]:
    if year is None:
        raise ScheduleParseError("A year is required. Re-run with --year YYYY.")
    rows = []
    with open(schedule_path, "r", encoding="utf-8") as schedule_file:
        for line_number, line in enumerate(schedule_file, start=1):
            if not line.strip() or line.lstrip().lower().startswith("day"):
                continue
            match = ROW_PATTERN.match(line)
            if not match:
                raise ScheduleParseError(
                    f"Could not parse schedule line {line_number}: {line.rstrip()}"
                )
            day = match.group("day").strip()
            date_text = match.group("date").strip()
            name = match.group("name").strip()
            try:
                start_time = parse_time(match.group("start"), date_text, year)
                end_time = parse_time(match.group("end"), date_text, year)
            except ScheduleParseError as exc:
                raise ScheduleParseError(
                    f"Could not parse schedule line {line_number}: {line.rstrip()} ({exc})"
                ) from exc
            if not name:
                raise ScheduleParseError(f"Missing event name on line {line_number}: {line.rstrip()}")
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
        rows = parse_schedule(schedule_path, year)
        existing_events = db.query(Event).order_by(Event.id).all()
        repair_events = [
            event for event in existing_events
            if not event.name.strip() or event.name.strip().lower() in {row["date_text"].lower() for row in rows}
        ]
        named_events = {
            event.name: event for event in existing_events
            if event not in repair_events and event.name.strip()
        }

        for index, row in enumerate(rows):
            event = named_events.get(row["name"])
            if event is None and index < len(repair_events):
                event = repair_events[index]
                event.name = row["name"]
                named_events[event.name] = event
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
    try:
        import_schedule(args.schedule_path, args.year)
    except (OSError, ScheduleParseError) as exc:
        print(f"Schedule import failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()