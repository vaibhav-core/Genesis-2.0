"""
Tests for student lookup and normalization (student_service.py).
"""

import pytest
from app.services.student_service import (
    normalize_roll,
    normalize_name,
    names_match,
    find_student_by_roll,
    find_students_by_name,
    verify_student_identity
)


class TestNormalization:
    """Test normalization functions."""
    
    def test_normalize_roll_uppercase(self):
        """Roll numbers are converted to uppercase."""
        assert normalize_roll("24me001") == "24ME001"
        assert normalize_roll("24ME001") == "24ME001"
    
    def test_normalize_roll_strip_whitespace(self):
        """Roll numbers are stripped of whitespace."""
        assert normalize_roll(" 24ME001 ") == "24ME001"
        assert normalize_roll("  24me001  ") == "24ME001"
    
    def test_normalize_name_strip(self):
        """Names are stripped but not case-changed."""
        assert normalize_name(" Rahul Kumar ") == "Rahul Kumar"
        assert normalize_name("Rahul Kumar") == "Rahul Kumar"
    
    def test_names_match_case_insensitive(self):
        """Name matching is case-insensitive."""
        assert names_match("Rahul Kumar", "rahul kumar")
        assert names_match("RAHUL KUMAR", "rahul kumar")
        assert names_match(" Rahul Kumar ", " RAHUL KUMAR ")
    
    def test_names_match_false(self):
        """Different names don't match."""
        assert not names_match("Rahul Kumar", "Priya Singh")
        assert not names_match("Rahul", "Kumar")


class TestStudentLookup:
    """Test student lookup functions."""
    
    def test_find_by_roll_exact_match(self, test_db, sample_students):
        """Find student by exact roll number match."""
        student = find_student_by_roll("24ME001", test_db)
        assert student is not None
        assert student.name == "Rahul Kumar"
    
    def test_find_by_roll_normalized(self, test_db, sample_students):
        """Find student by roll number with normalization."""
        # All these should find the same student
        s1 = find_student_by_roll("24me001", test_db)
        s2 = find_student_by_roll("24ME001", test_db)
        s3 = find_student_by_roll(" 24me001 ", test_db)
        
        assert s1 is not None
        assert s1.id == s2.id == s3.id
        assert s1.roll_number == "24ME001"
    
    def test_find_by_roll_not_found(self, test_db, sample_students):
        """Find returns None for non-existent roll number."""
        student = find_student_by_roll("99XX999", test_db)
        assert student is None
    
    def test_find_by_name_unique(self, test_db, sample_students):
        """Find student by unique name."""
        students = find_students_by_name("Priya Singh", test_db)
        assert len(students) == 1
        assert students[0].roll_number == "24ME002"
    
    def test_find_by_name_case_insensitive(self, test_db, sample_students):
        """Find student by name with case-insensitive matching."""
        s1 = find_students_by_name("priya singh", test_db)
        s2 = find_students_by_name("Priya Singh", test_db)
        s3 = find_students_by_name(" PRIYA SINGH ", test_db)
        
        assert len(s1) == len(s2) == len(s3) == 1
        assert s1[0].id == s2[0].id == s3[0].id
    
    def test_find_by_name_ambiguous(self, test_db, sample_students):
        """Find returns multiple results for ambiguous name."""
        students = find_students_by_name("Rahul Kumar", test_db)
        assert len(students) == 2
        assert set(s.roll_number for s in students) == {"24ME001", "24CS002"}
    
    def test_find_by_name_not_found(self, test_db, sample_students):
        """Find returns empty list for non-existent name."""
        students = find_students_by_name("Unknown Person", test_db)
        assert len(students) == 0


class TestStudentIdentityVerification:
    """Test student identity verification (roll + name)."""
    
    def test_verify_identity_valid(self, test_db, sample_students):
        """Valid roll + name verification succeeds."""
        is_valid, student = verify_student_identity("24ME001", "Rahul Kumar", test_db)
        assert is_valid
        assert student is not None
        assert student.roll_number == "24ME001"
    
    def test_verify_identity_normalized(self, test_db, sample_students):
        """Identity verification with normalized inputs."""
        is_valid, student = verify_student_identity(" 24me001 ", " rahul kumar ", test_db)
        assert is_valid
        assert student is not None
    
    def test_verify_identity_wrong_name(self, test_db, sample_students):
        """Identity verification fails with wrong name."""
        is_valid, student = verify_student_identity("24ME001", "Wrong Name", test_db)
        assert not is_valid
        assert student is None
    
    def test_verify_identity_unknown_roll(self, test_db, sample_students):
        """Identity verification fails with unknown roll."""
        is_valid, student = verify_student_identity("99XX999", "Rahul Kumar", test_db)
        assert not is_valid
        assert student is None
    
    def test_verify_identity_both_wrong(self, test_db, sample_students):
        """Identity verification fails with both wrong."""
        is_valid, student = verify_student_identity("99XX999", "Unknown Person", test_db)
        assert not is_valid
        assert student is None
