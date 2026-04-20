from __future__ import annotations

import pytest

from app.utils.normalizers import normalize_blank, normalize_identifier, normalize_name_for_match, normalize_whitespace


class TestNormalizeWhitespace:
    def test_collapses_spaces(self):
        assert normalize_whitespace('  foo   bar  ') == 'foo bar'

    def test_none_returns_none(self):
        assert normalize_whitespace(None) is None

    def test_empty_returns_none(self):
        assert normalize_whitespace('   ') is None


class TestNormalizeBlank:
    def test_strips_nan_strings(self):
        assert normalize_blank('nan') is None
        assert normalize_blank('NaN') is None
        assert normalize_blank('None') is None

    def test_keeps_real_values(self):
        assert normalize_blank('Paracetamol 500mg') == 'Paracetamol 500mg'

    def test_empty_string_returns_none(self):
        assert normalize_blank('') is None


class TestNormalizeIdentifier:
    def test_strips_float_suffix(self):
        assert normalize_identifier('12345.0') == '12345'

    def test_none_returns_none(self):
        assert normalize_identifier(None) is None

    def test_strips_whitespace(self):
        assert normalize_identifier('  ABC123  ') == 'ABC123'

    def test_integer_input(self):
        assert normalize_identifier(9876) == '9876'

    def test_empty_returns_none(self):
        assert normalize_identifier('') is None


class TestNormalizeNameForMatch:
    def test_lowercases(self):
        assert normalize_name_for_match('VITAMIN B12') == 'vitamin b12'

    def test_removes_punctuation(self):
        result = normalize_name_for_match('Vitamin B-12, 500mcg')
        assert ',' not in result
        assert '-' not in result

    def test_collapses_whitespace(self):
        assert normalize_name_for_match('foo   bar') == 'foo bar'

    def test_none_returns_none(self):
        assert normalize_name_for_match(None) is None

    def test_empty_returns_none(self):
        assert normalize_name_for_match('') is None
