
import pandas as pd
import pytest

from agents.report_agent import (
    generate_csv,
    generate_excel,
    generate_pdf,
)



@pytest.fixture
def report_dir(tmp_path, monkeypatch):
    # Run tests in an isolated temporary directory.
    monkeypatch.chdir(tmp_path)

    # The report functions write into this relative directory.
    reports = tmp_path / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    return reports


def test_generate_csv(report_dir):
    candidates = [
        {"name": "Amina", "score": 85, "recommendation": "Hire"},
        {"name": "Sara", "score": 62, "recommendation": "Second Round"},
    ]

    generate_csv(candidates)

    output = report_dir / "report.csv"
    assert output.exists()

    df = pd.read_csv(output)
    assert len(df) == 2
    assert df.iloc[0]["name"] == "Amina"
    assert df.iloc[0]["score"] == 85


def test_generate_csv_empty_candidates(report_dir):
    generate_csv([])

    output = report_dir / "report.csv"
    assert output.exists()


def test_generate_excel(report_dir):
    candidates = [
        {"name": "Amina", "score": 85, "recommendation": "Hire"}
    ]

    generate_excel(candidates)

    output = report_dir / "report.xlsx"
    assert output.exists()

    df = pd.read_excel(output)
    assert len(df) == 1
    assert df.iloc[0]["name"] == "Amina"
    assert df.iloc[0]["score"] == 85


def test_generate_excel_empty_candidates(report_dir):
    generate_excel([])

    output = report_dir / "report.xlsx"
    assert output.exists()


def test_generate_pdf(report_dir):
    candidates = [
        {"name": "Amina", "score": 85, "recommendation": "Hire"}
    ]

    generate_pdf(candidates)

    output = report_dir / "report.pdf"
    assert output.exists()
    assert output.read_bytes().startswith(b"%PDF")


def test_generate_pdf_empty_candidates(report_dir):
    generate_pdf([])

    output = report_dir / "report.pdf"
    assert output.exists()
    assert output.read_bytes().startswith(b"%PDF")


def test_generate_pdf_missing_optional_fields(report_dir):
    generate_pdf([{"name": "Amina"}])

    output = report_dir / "report.pdf"
    assert output.exists()
    assert output.stat().st_size > 0
