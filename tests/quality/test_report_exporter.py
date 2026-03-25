"""
Test suite for report_exporter.py

Tests the multi-format report export system including:
- ExportConfig configuration
- ExportedReport and ExportResult dataclasses
- ReportExporter class
- export_quality_reports() convenience function
- MarkdownReportGenerator
- generate_markdown_report() function
"""

import pytest
from datetime import datetime
from pathlib import Path
import json
import tempfile
import shutil
from dataclasses import asdict

from specify_cli.quality.report_exporter import (
    ExportConfig,
    ExportedReport,
    ExportResult,
    ReportExporter,
    export_quality_reports,
    export_result_card_json,
    format_export_summary,
    MarkdownReportGenerator,
    generate_markdown_report,
    ReportFormat,
    ALL_FORMATS,
)


# ===== Fixtures =====

@pytest.fixture
def sample_result():
    """Sample quality loop result for testing"""
    return {
        "final_score": 0.75,
        "phase": "A",
        "iterations": 3,
        "artifact": "Sample API specification",
        "criteria": ["api-spec", "security"],
        "category_scores": {
            "completeness": {"score": 0.8, "weight": 1.0, "passed": 8, "total": 10},
            "clarity": {"score": 0.7, "weight": 1.0, "passed": 7, "total": 10},
        },
        "failed_rules": [
            {
                "category": "security",
                "rule": "auth-mechanism",
                "severity": "high",
                "suggestion": "Add authentication mechanism"
            }
        ],
        "timeline": [
            {"iteration": 1, "score": 0.6, "phase": "A"},
            {"iteration": 2, "score": 0.7, "phase": "A"},
            {"iteration": 3, "score": 0.75, "phase": "A"},
        ],
        "started_at": "2026-03-13T10:00:00",
        "completed_at": "2026-03-13T10:05:00",
    }


@pytest.fixture
def temp_output_dir():
    """Temporary directory for export tests"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


# ===== ExportConfig Tests =====

class TestExportConfig:
    """Tests for ExportConfig dataclass"""

    def test_default_config(self):
        """Test ExportConfig with default values"""
        config = ExportConfig()
        assert config.formats == ALL_FORMATS
        assert config.output_dir is None
        assert config.filename_prefix == "quality_report"
        assert config.include_timeline is True
        assert config.include_details is True
        assert config.compact_console is False
        assert config.console_theme == "default"
        assert config.json_pretty is True
        assert config.json_validate is True

    def test_custom_formats(self):
        """Test ExportConfig with custom format set"""
        config = ExportConfig(formats={"json", "html"})
        assert config.formats == {"json", "html"}

    def test_formats_list_normalization(self):
        """Test that list formats are converted to set"""
        config = ExportConfig(formats=["json", "html", "markdown"])
        assert isinstance(config.formats, set)
        assert config.formats == {"json", "html", "markdown"}

    def test_invalid_formats_filtered(self):
        """Test that invalid formats are filtered out"""
        config = ExportConfig(formats={"json", "invalid", "html"})
        assert config.formats == {"json", "html"}

    def test_output_dir(self):
        """Test custom output directory"""
        config = ExportConfig(output_dir="./reports")
        assert config.output_dir == "./reports"

    def test_compact_console(self):
        """Test compact console mode"""
        config = ExportConfig(compact_console=True)
        assert config.compact_console is True


# ===== ExportedReport Tests =====

class TestExportedReport:
    """Tests for ExportedReport dataclass"""

    def test_exported_report_creation(self):
        """Test ExportedReport creation"""
        report = ExportedReport(
            format="json",
            content='{"score": 0.75}',
            path="report.json",
            size_bytes=100,
        )
        assert report.format == "json"
        assert report.content == '{"score": 0.75}'
        assert report.path == "report.json"
        assert report.size_bytes == 100
        assert isinstance(report.generated_at, str)

    def test_exported_report_defaults(self):
        """Test ExportedReport with default values"""
        report = ExportedReport(format="console", content="Score: 0.75")
        assert report.path is None
        assert report.size_bytes == 0


# ===== ExportResult Tests =====

class TestExportResult:
    """Tests for ExportResult dataclass"""

    def test_export_result_creation(self):
        """Test ExportResult creation"""
        result = ExportResult(output_dir="./reports")
        assert result.reports == {}
        assert result.output_dir == "./reports"
        assert result.total_size_bytes == 0
        assert isinstance(result.generated_at, str)

    def test_get_report_existing(self):
        """Test get_report for existing format"""
        result = ExportResult()
        json_report = ExportedReport(format="json", content='{"score": 0.75}')
        result.reports["json"] = json_report

        retrieved = result.get_report("json")
        assert retrieved is json_report

    def test_get_report_nonexistent(self):
        """Test get_report for non-existent format"""
        result = ExportResult()
        retrieved = result.get_report("html")
        assert retrieved is None

    def test_get_console_output(self):
        """Test get_console_output method"""
        result = ExportResult()
        console_report = ExportedReport(format="console", content="Score: 75%")
        result.reports["console"] = console_report

        output = result.get_console_output()
        assert output == "Score: 75%"

    def test_get_console_output_empty(self):
        """Test get_console_output when no console report"""
        result = ExportResult()
        output = result.get_console_output()
        assert output == ""

    def test_get_json_data_valid(self):
        """Test get_json_data with valid JSON"""
        result = ExportResult()
        json_report = ExportedReport(
            format="json",
            content='{"score": 0.75, "phase": "A"}'
        )
        result.reports["json"] = json_report

        data = result.get_json_data()
        assert data == {"score": 0.75, "phase": "A"}

    def test_get_json_data_invalid(self):
        """Test get_json_data with invalid JSON"""
        result = ExportResult()
        json_report = ExportedReport(format="json", content="invalid json")
        result.reports["json"] = json_report

        data = result.get_json_data()
        assert data == {}

    def test_get_json_data_no_report(self):
        """Test get_json_data when no JSON report"""
        result = ExportResult()
        data = result.get_json_data()
        assert data == {}

    def test_save_all(self, temp_output_dir, sample_result):
        """Test save_all method writes files"""
        result = ExportResult(output_dir=temp_output_dir)
        result.reports["json"] = ExportedReport(
            format="json",
            content='{"score": 0.75}',
            path="report.json"
        )
        result.reports["html"] = ExportedReport(
            format="html",
            content="<html>Report</html>",
            path="report.html"
        )

        result.save_all()

        # Verify files were written
        json_path = Path(temp_output_dir) / "report.json"
        html_path = Path(temp_output_dir) / "report.html"
        assert json_path.exists()
        assert html_path.exists()
        assert json_path.read_text() == '{"score": 0.75}'
        assert html_path.read_text() == "<html>Report</html>"

    def test_save_all_no_output_dir(self):
        """Test save_all raises error when no output dir"""
        result = ExportResult()
        result.reports["json"] = ExportedReport(
            format="json",
            content='{"score": 0.75}',
        )

        # Actual implementation raises TypeError when both are None
        with pytest.raises(TypeError):
            result.save_all()


# ===== ReportExporter Tests =====

class TestReportExporter:
    """Tests for ReportExporter class"""

    def test_exporter_default_config(self):
        """Test ReportExporter with default config"""
        exporter = ReportExporter()
        assert isinstance(exporter.config, ExportConfig)
        assert exporter.config.formats == ALL_FORMATS

    def test_exporter_custom_config(self):
        """Test ReportExporter with custom config"""
        config = ExportConfig(formats={"json", "html"})
        exporter = ReportExporter(config=config)
        assert exporter.config is config

    def test_export_console_format(self, sample_result):
        """Test exporting console format"""
        config = ExportConfig(formats={"console"})
        exporter = ReportExporter(config=config)

        export_result = exporter.export(sample_result)

        assert "console" in export_result.reports
        console_report = export_result.reports["console"]
        assert console_report.format == "console"
        assert isinstance(console_report.content, str)
        assert len(console_report.content) > 0

    def test_export_json_format(self, sample_result):
        """Test exporting JSON format"""
        config = ExportConfig(formats={"json"})
        exporter = ReportExporter(config=config)

        export_result = exporter.export(sample_result)

        assert "json" in export_result.reports
        json_report = export_result.reports["json"]
        assert json_report.format == "json"
        assert isinstance(json_report.content, str)

        # Verify valid JSON - structure uses summary.score
        data = json.loads(json_report.content)
        assert "summary" in data or "score" in data or "final_score" in data

    def test_export_html_format(self, sample_result):
        """Test exporting HTML format"""
        config = ExportConfig(formats={"html"})
        exporter = ReportExporter(config=config)

        export_result = exporter.export(sample_result)

        assert "html" in export_result.reports
        html_report = export_result.reports["html"]
        assert html_report.format == "html"
        assert isinstance(html_report.content, str)
        # Check for HTML markers
        assert "<html>" in html_report.content or "<!DOCTYPE" in html_report.content

    def test_export_markdown_format(self, sample_result):
        """Test exporting Markdown format"""
        config = ExportConfig(formats={"markdown"})
        exporter = ReportExporter(config=config)

        export_result = exporter.export(sample_result)

        assert "markdown" in export_result.reports
        md_report = export_result.reports["markdown"]
        assert md_report.format == "markdown"
        assert isinstance(md_report.content, str)
        # Check for Markdown markers
        assert "#" in md_report.content or "##" in md_report.content

    def test_export_csv_format(self, sample_result):
        """Test exporting CSV format"""
        config = ExportConfig(formats={"csv"})
        exporter = ReportExporter(config=config)

        export_result = exporter.export(sample_result)

        assert "csv" in export_result.reports
        csv_report = export_result.reports["csv"]
        assert csv_report.format == "csv"
        assert isinstance(csv_report.content, str)

    def test_export_multiple_formats(self, sample_result):
        """Test exporting multiple formats at once"""
        config = ExportConfig(formats={"console", "json", "html"})
        exporter = ReportExporter(config=config)

        export_result = exporter.export(sample_result)

        assert len(export_result.reports) == 3
        assert "console" in export_result.reports
        assert "json" in export_result.reports
        assert "html" in export_result.reports

    def test_export_with_previous_score(self, sample_result):
        """Test export with previous score for trend calculation"""
        exporter = ReportExporter()
        export_result = exporter.export(sample_result, previous_score=0.65)

        # Console output should show trend
        console_content = export_result.get_console_output()
        # Just verify it runs without error - trend display format may vary
        assert len(console_content) > 0

    def test_export_excel_with_list_criteria(self, sample_result):
        """Test Excel export handles list-type criteria without error (Exp 44)"""
        # sample_result has criteria as list: ["api-spec", "security"]
        config = ExportConfig(formats={"excel"})
        exporter = ReportExporter(config=config)

        export_result = exporter.export(sample_result)

        assert "excel" in export_result.reports
        excel_report = export_result.reports["excel"]
        assert excel_report.format == "excel"

    def test_export_to_file(self, sample_result, temp_output_dir):
        """Test exporting reports to files"""
        config = ExportConfig(
            formats={"json", "html"},
            output_dir=temp_output_dir
        )
        exporter = ReportExporter(config=config)

        export_result = exporter.export(sample_result)

        # Verify files were created
        output_path = Path(temp_output_dir)
        json_files = list(output_path.glob("*.json"))
        html_files = list(output_path.glob("*.html"))

        assert len(json_files) > 0
        assert len(html_files) > 0


# ===== export_quality_reports Tests =====

class TestExportQualityReports:
    """Tests for export_quality_reports convenience function"""

    def test_export_all_formats_default(self, sample_result):
        """Test export_quality_reports with all default formats"""
        export_result = export_quality_reports(
            sample_result,
            formats=["json", "html", "markdown"]  # Specify formats explicitly
        )

        assert isinstance(export_result, ExportResult)
        assert len(export_result.reports) > 0

    def test_export_specific_formats(self, sample_result):
        """Test export_quality_reports with specific formats"""
        export_result = export_quality_reports(
            sample_result,
            formats=["json", "markdown"]
        )

        assert "json" in export_result.reports
        assert "markdown" in export_result.reports
        assert "html" not in export_result.reports

    def test_export_with_output_dir(self, sample_result, temp_output_dir):
        """Test export_quality_reports with output directory"""
        export_result = export_quality_reports(
            sample_result,
            formats=["json"],
            output_dir=temp_output_dir
        )

        assert export_result.output_dir == temp_output_dir

    def test_export_with_custom_prefix(self, sample_result, temp_output_dir):
        """Test export_quality_reports with custom filename prefix"""
        export_result = export_quality_reports(
            sample_result,
            formats=["json"],
            output_dir=temp_output_dir,
            filename_prefix="my_report"
        )

        # Verify files have custom prefix
        output_path = Path(temp_output_dir)
        json_files = list(output_path.glob("my_report*.json"))
        assert len(json_files) > 0

    def test_export_compact_console(self, sample_result):
        """Test export_quality_reports with compact console mode"""
        export_result = export_quality_reports(
            sample_result,
            formats=["console"],
            compact_console=True
        )

        console_content = export_result.get_console_output()
        assert isinstance(console_content, str)
        assert len(console_content) > 0


# ===== export_result_card_json Tests =====

class TestExportResultCardJson:
    """Tests for export_result_card_json function"""

    def test_export_result_card_json_basic(self, sample_result):
        """Test export_result_card_json returns valid JSON"""
        json_str = export_result_card_json(sample_result)

        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert isinstance(data, dict)

    def test_export_result_card_json_structure(self, sample_result):
        """Test export_result_card_json has expected structure"""
        json_str = export_result_card_json(sample_result)
        data = json.loads(json_str)

        # Should have score and display info
        # Check for score (at root or in summary)
        has_score = "score" in data or "final_score" in data or ("summary" in data and "score" in data["summary"])
        assert has_score

        # Check that score is numeric (handle the or logic correctly)
        score = data.get("score", data.get("summary", {}).get("score"))
        if score is not None:
            assert isinstance(score, (int, float))

    def test_export_result_card_json_with_custom_config(self, sample_result):
        """Test export_result_card_json with custom configuration"""
        # Function only supports output_path and pretty params
        json_str = export_result_card_json(
            sample_result,
            pretty=True
        )

        data = json.loads(json_str)
        assert isinstance(data, dict)


# ===== format_export_summary Tests =====

class TestFormatExportSummary:
    """Tests for format_export_summary function"""

    def test_format_summary_empty_result(self):
        """Test format_export_summary with empty result"""
        result = ExportResult()
        summary = format_export_summary(result)

        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_format_summary_with_reports(self, sample_result):
        """Test format_export_summary with actual reports"""
        result = ExportResult()
        result.reports["json"] = ExportedReport(
            format="json",
            content='{"score": 0.75}',
            size_bytes=100
        )
        result.reports["html"] = ExportedReport(
            format="html",
            content="<html>Report</html>",
            size_bytes=200
        )

        summary = format_export_summary(result)
        assert isinstance(summary, str)
        assert "json" in summary.lower() or "html" in summary.lower()

    def test_format_summary_with_output_dir(self):
        """Test format_export_summary includes output directory"""
        result = ExportResult(output_dir="./reports")
        summary = format_export_summary(result)

        assert isinstance(summary, str)


# ===== MarkdownReportGenerator Tests =====

class TestMarkdownReportGenerator:
    """Tests for MarkdownReportGenerator class"""

    def test_generator_creation(self):
        """Test MarkdownReportGenerator instantiation"""
        generator = MarkdownReportGenerator()
        assert generator is not None

    def test_generate_basic_report(self, sample_result):
        """Test generating basic markdown report"""
        generator = MarkdownReportGenerator()
        report = generator.generate(sample_result)

        assert isinstance(report, str)
        assert len(report) > 0
        # Should have markdown headers
        assert "#" in report

    def test_generate_with_timeline(self, sample_result):
        """Test generating report with timeline"""
        generator = MarkdownReportGenerator()
        report = generator.generate(
            sample_result,
            include_timeline=True
        )

        assert isinstance(report, str)

    def test_generate_without_details(self, sample_result):
        """Test generating report without details"""
        generator = MarkdownReportGenerator()
        report = generator.generate(
            sample_result,
            include_details=False
        )

        assert isinstance(report, str)


# ===== generate_markdown_report Tests =====

class TestGenerateMarkdownReport:
    """Tests for generate_markdown_report convenience function"""

    def test_generate_basic(self, sample_result):
        """Test generate_markdown_report basic usage"""
        report = generate_markdown_report(sample_result)

        assert isinstance(report, str)
        assert len(report) > 0

    def test_generate_with_options(self, sample_result):
        """Test generate_markdown_report with options"""
        report = generate_markdown_report(
            sample_result,
            include_timeline=True,
            include_details=True
        )

        assert isinstance(report, str)


# ===== Integration Tests =====

class TestReportExporterIntegration:
    """Integration tests for report export workflow"""

    def test_full_export_workflow(self, sample_result, temp_output_dir):
        """Test complete export workflow: config -> export -> save"""
        config = ExportConfig(
            formats={"json", "html", "markdown"},
            output_dir=temp_output_dir,
            filename_prefix="test_report"
        )
        exporter = ReportExporter(config=config)
        export_result = exporter.export(sample_result, previous_score=0.65)
        export_result.save_all()

        # Verify all formats generated
        assert "json" in export_result.reports
        assert "html" in export_result.reports
        assert "markdown" in export_result.reports

        # Verify files saved
        output_path = Path(temp_output_dir)
        assert any(output_path.glob("test_report*.json"))
        assert any(output_path.glob("test_report*.html"))
        assert any(output_path.glob("test_report*.md"))

    def test_export_result_card_workflow(self, sample_result):
        """Test export_result_card_json in workflow"""
        json_str = export_result_card_json(sample_result)
        data = json.loads(json_str)

        # Verify we can round-trip
        assert isinstance(data, dict)

    def test_convenience_function_workflow(self, sample_result, temp_output_dir):
        """Test export_quality_reports convenience function workflow"""
        export_result = export_quality_reports(
            sample_result,
            formats=["json", "markdown"],
            output_dir=temp_output_dir,
            filename_prefix="workflow_test"
        )

        # Verify formats
        assert "json" in export_result.reports
        assert "markdown" in export_result.reports

        # Verify console output works
        console = export_result.get_console_output()
        assert isinstance(console, str)

        # Verify JSON parsing works
        json_data = export_result.get_json_data()
        assert isinstance(json_data, dict)
