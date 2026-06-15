"""Shared test fixtures for ModelProbe."""

import pytest


class NoOpBackend:
    """Backend that silently discards all writes. Use in unit tests."""

    def write_run(self, run):
        pass

    def get_run(self, run_id):
        return None

    def list_runs(self, filters=None):
        return []

    def write_eval_result(self, result):
        pass

    def write_test_case(self, tc):
        pass

    def list_test_cases(self, suite):
        return []

    def list_eval_results(self, run_id):
        return []

    def list_suites(self):
        return []


class CapturingBackend:
    """Backend that captures all written records in memory."""

    def __init__(self):
        self.runs = []
        self.eval_results = []
        self.test_cases = []

    def write_run(self, run):
        self.runs.append(dict(run))

    def get_run(self, run_id):
        return next((r for r in self.runs if r["id"] == run_id), None)

    def list_runs(self, filters=None):
        return list(self.runs)

    def write_eval_result(self, result):
        self.eval_results.append(dict(result))

    def write_test_case(self, tc):
        self.test_cases.append(dict(tc))

    def list_test_cases(self, suite):
        return [tc for tc in self.test_cases if tc.get("suite") == suite]

    def list_eval_results(self, run_id):
        return [r for r in self.eval_results if r.get("run_id") == run_id]

    def list_suites(self):
        return list({r["suite"] for r in self.runs})
