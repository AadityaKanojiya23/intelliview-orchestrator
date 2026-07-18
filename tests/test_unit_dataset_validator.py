"""Unit tests for scripts/dataset_validation/validator.py"""

import pytest

from scripts.dataset_validation.schemas import QUESTION_BANK_SCHEMA, EVALUATION_DATASET_SCHEMA
from scripts.dataset_validation.validator import DatasetValidator


@pytest.fixture
def valid_questions():
    return [
        {"question_id": "q_001", "text": "Describe your experience with distributed systems.",
         "category": "technical", "difficulty": "medium", "usage_count": 12, "avg_score": 78.5},
        {"question_id": "q_002", "text": "Tell me about a time you disagreed with a teammate.",
         "category": "behavioral", "difficulty": "easy", "usage_count": 5, "avg_score": 82.0},
        {"question_id": "q_003", "text": "How would you design a rate limiter for a public API?",
         "category": "technical", "difficulty": "hard", "usage_count": 3, "avg_score": 65.2},
    ]


class TestQuestionBankValidator:
    def test_valid_dataset_passes(self, valid_questions):
        report = DatasetValidator(QUESTION_BANK_SCHEMA).validate(valid_questions)
        assert report.is_valid
        assert len(report.errors) == 0

    def test_empty_dataset_fails(self):
        report = DatasetValidator(QUESTION_BANK_SCHEMA).validate([])
        assert not report.is_valid
        assert any(r.rule_name == "non_empty_dataset" for r in report.errors)

    def test_missing_required_field_fails(self, valid_questions):
        broken = [dict(valid_questions[0])]
        del broken[0]["text"]
        report = DatasetValidator(QUESTION_BANK_SCHEMA).validate(broken)
        assert not report.is_valid
        assert any(r.rule_name == "required_fields_present" for r in report.errors)

    def test_invalid_enum_value_fails(self, valid_questions):
        broken = [dict(valid_questions[0], category="not_a_real_category")]
        report = DatasetValidator(QUESTION_BANK_SCHEMA).validate(broken)
        assert not report.is_valid
        assert any(r.rule_name == "enum_values_valid" for r in report.errors)

    def test_out_of_range_score_fails(self, valid_questions):
        broken = [dict(valid_questions[0], avg_score=150)]
        report = DatasetValidator(QUESTION_BANK_SCHEMA).validate(broken)
        assert not report.is_valid
        assert any(r.rule_name == "numeric_ranges_valid" for r in report.errors)

    def test_duplicate_ids_fail(self, valid_questions):
        broken = valid_questions + [dict(valid_questions[0])]
        report = DatasetValidator(QUESTION_BANK_SCHEMA).validate(broken)
        assert not report.is_valid
        assert any(r.rule_name == "unique_ids" for r in report.errors)

    def test_near_duplicate_text_warns_but_does_not_fail(self, valid_questions):
        near_dupe = dict(valid_questions[0], question_id="q_099",
                          text="Describe your experience with distributed systems!!")
        report = DatasetValidator(QUESTION_BANK_SCHEMA).validate(valid_questions + [near_dupe])
        dup_result = next(r for r in report.results if r.rule_name == "no_near_duplicates")
        assert dup_result.severity == "warning"
        assert not dup_result.passed
        # warnings alone should not flip overall validity
        assert report.is_valid

    def test_class_imbalance_warns(self, valid_questions):
        skewed = [dict(valid_questions[0], question_id=f"q_{i}") for i in range(20)]
        skewed.append(valid_questions[1])  # 1 behavioral vs 20 technical
        report = DatasetValidator(QUESTION_BANK_SCHEMA).validate(skewed)
        balance_result = next(r for r in report.results if r.rule_name == "class_balance")
        assert not balance_result.passed


class TestEvaluationDatasetValidator:
    def test_valid_eval_sample_passes(self):
        records = [
            {"sample_id": "e_001", "question": "What is a race condition?",
             "answer": "It happens when threads access shared state unsynchronized.",
             "expected_label": "grounded", "expected_score": 90},
        ]
        report = DatasetValidator(EVALUATION_DATASET_SCHEMA).validate(records)
        assert report.is_valid

    def test_invalid_label_fails(self):
        records = [
            {"sample_id": "e_001", "question": "What is a race condition?",
             "answer": "It happens when threads access shared state unsynchronized.",
             "expected_label": "maybe_true"},
        ]
        report = DatasetValidator(EVALUATION_DATASET_SCHEMA).validate(records)
        assert not report.is_valid
        assert any(r.rule_name == "enum_values_valid" for r in report.errors)


def test_report_serializes_to_dict(valid_questions):
    report = DatasetValidator(QUESTION_BANK_SCHEMA).validate(valid_questions)
    d = report.to_dict()
    assert d["total_records"] == 3
    assert d["is_valid"] is True
    assert isinstance(d["checks"], list)