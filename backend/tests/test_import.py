"""
Tests for student import script.
"""

import pytest
import sys
import tempfile
import csv
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from app.database import Base
from app.models import Student, Event
from import_students import import_students
from import_schedule import ScheduleParseError, import_schedule


class TestStudentImport:
    """Test student import from CSV."""

    @pytest.fixture
    def import_session_factory(self):
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=engine)
        session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
        )
        yield session_factory
        engine.dispose()
    
    def test_import_basic(self, import_session_factory):
        """Import basic CSV with roll and name."""
        # Create temporary CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['Roll Number', 'Name', 'Branch', 'Year'])
            writer.writerow(['24ME001', 'Rahul Kumar', 'Mechanical', '1'])
            writer.writerow(['24ME002', 'Priya Singh', 'Mechanical', '1'])
            csv_path = f.name
        
        try:
            # Import
            import_students(csv_path, session_factory=import_session_factory)
            
            # Verify
            db = import_session_factory()
            students = db.query(Student).all()
            db.close()
            
            assert len(students) == 2
            assert students[0].roll_number == "24ME001"
            assert students[0].name == "Rahul Kumar"
        finally:
            Path(csv_path).unlink()
    def test_import_idempotent(self, import_session_factory):
        """Import same CSV twice should skip duplicates."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['Roll Number', 'Name', 'Branch', 'Year'])
            writer.writerow(['24ME001', 'Rahul Kumar', 'Mechanical', '1'])
            csv_path = f.name
        
        try:
            # First import
            import_students(csv_path, session_factory=import_session_factory)
            
            # Verify first import
            db = import_session_factory()
            count1 = db.query(Student).count()
            db.close()
            assert count1 == 1
            
            # Second import (same file)
            import_students(csv_path, session_factory=import_session_factory)
            
            # Verify second import skipped duplicates
            db = import_session_factory()
            count2 = db.query(Student).count()
            db.close()
            assert count2 == 1  # No new students added
        finally:
            Path(csv_path).unlink()


class TestScheduleImport:
    @pytest.fixture
    def import_session_factory(self):
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=engine)
        yield sessionmaker(autocommit=False, autoflush=False, bind=engine)
        engine.dispose()

    @pytest.fixture
    def schedule_file(self, tmp_path):
        path = tmp_path / "schedule.txt"
        path.write_text(
            "DAY\tDate\tEvent Name\tTime Stamps\n"
            "Saturday\t12-sept\t\tCipher\t\t8:00 am to 1:00 pm\n"
            "Sunday\t13-sept\t\tDance\t\t1:30pm to 2:00 pm\n",
            encoding="utf-8",
        )
        return path

    def test_schedule_import_is_idempotent(self, import_session_factory, schedule_file):
        expected_names = ["Cipher", "Dance"]
        import_schedule(str(schedule_file), year=2026, session_factory=import_session_factory)
        import_schedule(str(schedule_file), year=2026, session_factory=import_session_factory)
        db = import_session_factory()
        events = db.query(Event).order_by(Event.id).all()
        db.close()
        assert [event.name for event in events] == expected_names
        assert len(events) == len(expected_names)
        assert all(event.start_time is not None and event.end_time is not None for event in events)

    def test_schedule_import_requires_year(self, import_session_factory, schedule_file):
        with pytest.raises(ScheduleParseError, match="year"):
            import_schedule(str(schedule_file), session_factory=import_session_factory)

    def test_schedule_import_rejects_malformed_rows(self, import_session_factory, tmp_path):
        path = tmp_path / "bad-schedule.txt"
        path.write_text("Saturday\t12-sept\t\tMissing time\n", encoding="utf-8")
        with pytest.raises(ScheduleParseError, match="line 1"):
            import_schedule(str(path), year=2026, session_factory=import_session_factory)

    def test_import_flexible_headers(self, import_session_factory):
        """Import with flexible header variants."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            # Use variant headers
            writer.writerow(['roll_number', 'Name'])  # lowercase, underscore
            writer.writerow(['24ME001', 'Rahul Kumar'])
            csv_path = f.name
        
        try:
            import_students(csv_path, session_factory=import_session_factory)
            
            db = import_session_factory()
            student = db.query(Student).first()
            db.close()
            
            assert student is not None
            assert student.roll_number == "24ME001"
        finally:
            Path(csv_path).unlink()
    
    def test_import_skips_invalid_rows(self, import_session_factory):
        """Import skips rows with missing roll or name."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['Roll Number', 'Name', 'Branch'])
            writer.writerow(['24ME001', 'Rahul Kumar', 'Mechanical'])
            writer.writerow(['', 'No Roll', 'Mechanical'])  # Missing roll
            writer.writerow(['24ME003', '', 'Mechanical'])  # Missing name
            writer.writerow(['24ME004', 'Valid Student', 'Mechanical'])
            csv_path = f.name
        
        try:
            import_students(csv_path, session_factory=import_session_factory)
            
            db = import_session_factory()
            students = db.query(Student).all()
            db.close()
            
            assert len(students) == 2  # Only valid rows
            rolls = {s.roll_number for s in students}
            assert rolls == {"24ME001", "24ME004"}
        finally:
            Path(csv_path).unlink()
    
    def test_import_normalizes_roll(self, import_session_factory):
        """Import normalizes roll numbers to uppercase."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['Roll Number', 'Name'])
            writer.writerow(['24me001', 'Rahul Kumar'])  # lowercase
            writer.writerow([' 24ME002 ', 'Priya Singh'])  # whitespace
            csv_path = f.name
        
        try:
            import_students(csv_path, session_factory=import_session_factory)
            
            db = import_session_factory()
            students = db.query(Student).order_by(Student.roll_number).all()
            db.close()
            
            assert students[0].roll_number == "24ME001"  # Uppercase
            assert students[1].roll_number == "24ME002"  # Whitespace trimmed
        finally:
            Path(csv_path).unlink()
    
    def test_import_missing_required_column(self, import_session_factory):
        """Import aborts if required column can't be found."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['Roll Number'])  # Missing Name
            writer.writerow(['24ME001'])
            csv_path = f.name
        
        try:
            # Should exit with error
            with pytest.raises(SystemExit):
                import_students(csv_path, session_factory=import_session_factory)
        finally:
            Path(csv_path).unlink()
