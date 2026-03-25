"""
Core unit tests for the Autonomous SRE Engine.
Run with: pytest tests/test_core.py -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from analysis.signals.signal_analyzer import SignalAnalyzer
from analysis.reasoning.failure_predictor import FailurePredictor
from analysis.signals.time_analyzer import TemporalAnalyzer
from analysis.reasoning.root_cause_engine import RootCauseEngine
from analysis.reasoning.dependency_graph import DependencyGraph
from actions.safety_guard import ActionSafetyGuard
from actions.action import Action, ActionType


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def make_signal(entity_id, signal, confidence, metric="cpu_usage", reason="test"):
    return {
        "entity_id": entity_id,
        "metric": metric,
        "signal": signal,
        "confidence": confidence,
        "reason": reason
    }

def make_action(action_type=ActionType.LOCKDOWN, target="node-1"):
    return Action(
        action_type=action_type,
        target=target,
        reason="test reason",
        confidence=0.9
    )

def make_temporal(trend="worsening", persistence=5, volatility=0.1):
    return {
        "trend": trend,
        "persistence": persistence,
        "volatility": volatility,
        "slope": 0.1
    }

def make_history(values):
    """Wrap plain risk values as (timestamp, risk) tuples like TemporalMemory produces."""
    return [(i, v) for i, v in enumerate(values)]


# --------------------------------------------------
# SIGNAL ANALYZER
# --------------------------------------------------

class TestSignalAnalyzer:

    def setup_method(self):
        self.analyzer = SignalAnalyzer()

    def test_critical_state_on_high_risk(self):
        signals = [make_signal("node-1", 0.95, 1.0)]
        result = self.analyzer.analyze(signals)
        assert result["node-1"]["state"] == "CRITICAL"
        assert result["node-1"]["risk_score"] >= 0.85

    def test_degraded_state_on_medium_risk(self):
        signals = [make_signal("node-1", 0.7, 1.0)]
        result = self.analyzer.analyze(signals)
        assert result["node-1"]["state"] == "DEGRADED"

    def test_warning_state(self):
        signals = [make_signal("node-1", 0.4, 1.0)]
        result = self.analyzer.analyze(signals)
        assert result["node-1"]["state"] == "WARNING"

    def test_healthy_state_on_low_risk(self):
        signals = [make_signal("node-1", 0.1, 1.0)]
        result = self.analyzer.analyze(signals)
        assert result["node-1"]["state"] == "HEALTHY"

    def test_multiple_entities_isolated(self):
        signals = [
            make_signal("node-1", 0.95, 1.0),
            make_signal("node-2", 0.1, 1.0),
        ]
        result = self.analyzer.analyze(signals)
        assert result["node-1"]["state"] == "CRITICAL"
        assert result["node-2"]["state"] == "HEALTHY"

    def test_weighted_risk_across_signals(self):
        """Risk = weighted average — higher confidence signals dominate."""
        signals = [
            make_signal("node-1", 0.9, 0.9, metric="cpu_usage"),
            make_signal("node-1", 0.1, 0.1, metric="disk_usage"),
        ]
        result = self.analyzer.analyze(signals)
        # Weighted: (0.9*0.9 + 0.1*0.1) / (0.9+0.1) = 0.82
        assert result["node-1"]["risk_score"] == pytest.approx(0.82, abs=0.01)

    def test_zero_confidence_signals_return_zero_risk(self):
        signals = [make_signal("node-1", 0.99, 0.0)]
        result = self.analyzer.analyze(signals)
        assert result["node-1"]["risk_score"] == 0.0

    def test_empty_signals_returns_empty(self):
        result = self.analyzer.analyze([])
        assert result == {}

    def test_explanation_included_in_result(self):
        signals = [make_signal("node-1", 0.9, 1.0, reason="cpu spike detected")]
        result = self.analyzer.analyze(signals)
        assert any("cpu spike detected" in e for e in result["node-1"]["explanation"])


# --------------------------------------------------
# FAILURE PREDICTOR
# --------------------------------------------------

class TestFailurePredictor:

    def setup_method(self):
        self.predictor = FailurePredictor()

    def test_empty_history_returns_zero(self):
        result = self.predictor.predict([])
        assert result["risk_forecast"] == 0
        assert result["trend"] == "stable"

    def test_short_history_returns_last_value(self):
        result = self.predictor.predict(make_history([0.3, 0.5]))
        assert result["risk_forecast"] == pytest.approx(0.5, abs=0.01)

    def test_increasing_trend_detected(self):
        history = make_history([0.1, 0.3, 0.5, 0.7, 0.9])
        result = self.predictor.predict(history)
        assert result["trend"] == "increasing"

    def test_decreasing_trend_detected(self):
        history = make_history([0.9, 0.7, 0.5, 0.3, 0.1])
        result = self.predictor.predict(history)
        assert result["trend"] == "decreasing"

    def test_stable_trend_detected(self):
        history = make_history([0.5, 0.5, 0.5, 0.5, 0.5])
        result = self.predictor.predict(history)
        assert result["trend"] == "stable"

    def test_forecast_clamped_to_zero_minimum(self):
        history = make_history([0.3, 0.2, 0.1, 0.05, 0.01])
        result = self.predictor.predict(history)
        assert result["risk_forecast"] >= 0.0

    def test_forecast_clamped_to_one_maximum(self):
        history = make_history([0.7, 0.8, 0.9, 0.95, 0.99])
        result = self.predictor.predict(history)
        assert result["risk_forecast"] <= 1.0

    def test_tuple_history_handled(self):
        """TemporalMemory stores (timestamp, risk) tuples — predictor must handle both."""
        history = [(0, 0.2), (1, 0.4), (2, 0.6), (3, 0.8)]
        result = self.predictor.predict(history)
        assert result["trend"] == "increasing"

    def test_forecast_is_rounded(self):
        history = make_history([0.1, 0.3, 0.5, 0.7, 0.9])
        result = self.predictor.predict(history)
        # Should be rounded to 3 decimal places
        assert result["risk_forecast"] == round(result["risk_forecast"], 3)


# --------------------------------------------------
# TEMPORAL ANALYZER
# --------------------------------------------------

class TestTemporalAnalyzer:

    def setup_method(self):
        self.analyzer = TemporalAnalyzer()

    def test_insufficient_data(self):
        result = self.analyzer.analyze([(0, 0.5), (1, 0.6)])
        assert result["trend"] == "insufficient_data"
        assert result["persistence"] == 2

    def test_worsening_trend(self):
        history = [(i, v) for i, v in enumerate([0.1, 0.5, 0.9])]
        result = self.analyzer.analyze(history)
        assert result["trend"] == "worsening"

    def test_improving_trend(self):
        history = [(i, v) for i, v in enumerate([0.9, 0.5, 0.1])]
        result = self.analyzer.analyze(history)
        assert result["trend"] == "improving"

    def test_stable_trend(self):
        history = [(i, v) for i, v in enumerate([0.5, 0.5, 0.5])]
        result = self.analyzer.analyze(history)
        assert result["trend"] == "stable"

    def test_persistence_counts_high_risk_entries(self):
        """Persistence = number of readings above 0.7."""
        history = [(i, v) for i, v in enumerate([0.8, 0.9, 0.3, 0.75, 0.5])]
        result = self.analyzer.analyze(history)
        assert result["persistence"] == 3

    def test_volatility_is_nonnegative(self):
        history = [(i, v) for i, v in enumerate([0.2, 0.8, 0.3, 0.9, 0.1])]
        result = self.analyzer.analyze(history)
        assert result["volatility"] >= 0.0


# --------------------------------------------------
# ROOT CAUSE ENGINE
# --------------------------------------------------

class TestRootCauseEngine:

    def setup_method(self):
        self.graph = DependencyGraph()
        self.engine = RootCauseEngine(self.graph)

    def _make_health(self, states):
        """states: dict of entity_id -> state string"""
        return {
            eid: {"state": state, "risk_score": 0.9 if state == "CRITICAL" else 0.3}
            for eid, state in states.items()
        }

    def test_no_critical_returns_none(self):
        health = self._make_health({"flask-server": "HEALTHY", "proc-python3": "HEALTHY"})
        assert self.engine.find_root_cause(health) == None

    def test_single_critical_returns_itself(self):
        health = self._make_health({"flask-server": "CRITICAL"})
        result = self.engine.find_root_cause(health)
        assert result == "flask-server"

    def test_upstream_dependency_identified_as_root_cause(self):
        """flask-server depends on proc-python3 — if both CRITICAL, proc-python3 is root."""
        health = self._make_health({
            "flask-server": "CRITICAL",
            "proc-python3": "CRITICAL"
        })
        result = self.engine.find_root_cause(health)
        assert result == "proc-python3"

    def test_healthy_dependency_not_returned_as_root_cause(self):
        health = self._make_health({
            "flask-server": "CRITICAL",
            "proc-python3": "HEALTHY"
        })
        result = self.engine.find_root_cause(health)
        assert result == "flask-server"

    def test_case_sensitive_state_matching(self):
        """Regression: lowercase 'critical' must NOT match."""
        health = {
            "flask-server": {"state": "CRITICAL", "risk_score": 0.9},
            "proc-python3": {"state": "critical", "risk_score": 0.9},  # wrong case
        }
        result = self.engine.find_root_cause(health)
        # proc-python3 has wrong case so should NOT be identified as root cause
        assert result == "flask-server"


# --------------------------------------------------
# ACTION SAFETY GUARD
# --------------------------------------------------

class TestActionSafetyGuard:

    def setup_method(self):
        self.guard = ActionSafetyGuard()
        self.action = make_action()

    def test_allows_valid_action(self):
        temporal = make_temporal(trend="worsening", persistence=5, volatility=0.1)
        assert self.guard.allow(self.action, temporal) == True

    def test_blocks_when_improving(self):
        temporal = make_temporal(trend="improving", persistence=5, volatility=0.1)
        assert self.guard.allow(self.action, temporal) == False

    def test_blocks_insufficient_persistence(self):
        temporal = make_temporal(trend="worsening", persistence=2, volatility=0.1)
        assert self.guard.allow(self.action, temporal) == False

    def test_blocks_high_volatility(self):
        temporal = make_temporal(trend="worsening", persistence=5, volatility=0.5)
        assert self.guard.allow(self.action, temporal) == False

    def test_blocks_at_persistence_boundary(self):
        """Exactly 3 persistence should be blocked (< 3 is the condition)."""
        temporal = make_temporal(trend="worsening", persistence=2, volatility=0.1)
        assert self.guard.allow(self.action, temporal) == False

    def test_allows_at_persistence_threshold(self):
        temporal = make_temporal(trend="worsening", persistence=3, volatility=0.1)
        assert self.guard.allow(self.action, temporal) == True

    def test_returns_bool_not_tuple(self):
        """Regression: old code returned (bool, bool) tuple."""
        temporal = make_temporal()
        result = self.guard.allow(self.action, temporal)
        assert isinstance(result, bool), "allow() must return a single bool, not a tuple"