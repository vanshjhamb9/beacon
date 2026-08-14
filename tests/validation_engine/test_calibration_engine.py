"""Tests for CalibrationEngine."""

from __future__ import annotations

from validation_engine.calibration_engine import CalibrationEngine


class TestCalibrationEngineGetCalibrationSummary:
    def test_empty_summary(self, calibration_engine: CalibrationEngine) -> None:
        summary = calibration_engine.get_calibration_summary()
        assert "connector_ranking" in summary
        assert "industry_ranking" in summary
        assert "service_ranking" in summary
        assert "persona_ranking" in summary
        assert "trigger_ranking" in summary
        assert summary["total_revenue"] == 0.0
        assert summary["win_rate"] == 0.0

    def test_summary_with_data(self, calibration_engine: CalibrationEngine) -> None:
        calibration_engine.connector_roi.record_deal("linkedin", revenue=50000.0)
        calibration_engine.industry_roi.record_deal("healthcare", revenue=100000.0)
        calibration_engine.service_roi.record_deal("ai_automation", revenue=75000.0)
        calibration_engine.deal_tracker.record_deal("company_1", "won", revenue=100000.0)
        summary = calibration_engine.get_calibration_summary()
        assert len(summary["connector_ranking"]) > 0
        assert len(summary["industry_ranking"]) > 0
        assert len(summary["service_ranking"]) > 0
        assert summary["total_revenue"] == 100000.0


class TestCalibrationEngineGetConnectorCalibration:
    def test_empty_connector_calibration(self, calibration_engine: CalibrationEngine) -> None:
        result = calibration_engine.get_connector_calibration()
        assert result == []

    def test_connector_calibration_with_data(self, calibration_engine: CalibrationEngine) -> None:
        calibration_engine.connector_roi.record_deal("linkedin", revenue=50000.0)
        calibration_engine.connector_roi.record_deal("github", revenue=10000.0)
        result = calibration_engine.get_connector_calibration()
        assert len(result) == 2
        assert result[0]["connector"] == "linkedin"
        assert result[0]["revenue"] == 50000.0


class TestCalibrationEngineGetIndustryCalibration:
    def test_empty_industry_calibration(self, calibration_engine: CalibrationEngine) -> None:
        result = calibration_engine.get_industry_calibration()
        assert result == []

    def test_industry_calibration_with_data(self, calibration_engine: CalibrationEngine) -> None:
        calibration_engine.industry_roi.record_deal("healthcare", revenue=100000.0)
        result = calibration_engine.get_industry_calibration()
        assert len(result) == 1
        assert result[0]["industry"] == "healthcare"


class TestCalibrationEngineGetServiceCalibration:
    def test_empty_service_calibration(self, calibration_engine: CalibrationEngine) -> None:
        result = calibration_engine.get_service_calibration()
        assert result == []

    def test_service_calibration_with_data(self, calibration_engine: CalibrationEngine) -> None:
        calibration_engine.service_roi.record_deal("ai_automation", revenue=75000.0)
        result = calibration_engine.get_service_calibration()
        assert len(result) == 1
        assert result[0]["service"] == "ai_automation"


class TestCalibrationEngineGetPersonaCalibration:
    def test_empty_persona_calibration(self, calibration_engine: CalibrationEngine) -> None:
        result = calibration_engine.get_persona_calibration()
        assert result == []

    def test_persona_calibration_with_data(self, calibration_engine: CalibrationEngine) -> None:
        calibration_engine.persona_roi.record_deal("founder", revenue=100000.0)
        result = calibration_engine.get_persona_calibration()
        assert len(result) == 1
        assert result[0]["persona"] == "founder"


class TestCalibrationEngineGetTriggerCalibration:
    def test_empty_trigger_calibration(self, calibration_engine: CalibrationEngine) -> None:
        result = calibration_engine.get_trigger_calibration()
        assert result == []

    def test_trigger_calibration_with_data(self, calibration_engine: CalibrationEngine) -> None:
        calibration_engine.trigger_roi.record_deal("funding", revenue=100000.0)
        result = calibration_engine.get_trigger_calibration()
        assert len(result) == 1
        assert result[0]["trigger"] == "funding"
