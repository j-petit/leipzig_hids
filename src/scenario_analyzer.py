"""
File: scenario_analyzer.py
Author: Jens Petit
Email: petit@informatik.uni-leipzig.de
Description: Class for analyzing a scenario
"""

from sklearn.metrics import precision_recall_curve
from sklearn.metrics import precision_score
from sklearn.metrics import classification_report
import pandas as pd
import numpy as np
import pudb
import logging


class ScenarioAnalyzer(object):
    """The ScenarioAnalyzer"""

    def __init__(self, threshold, sacred_run, runs):
        super(ScenarioAnalyzer, self).__init__()

        self.threshold = threshold

        self.results = []

        self.sacred_run = sacred_run

        self.runs = runs.copy()

        self.processed_results = None

    def add_run(self, run_result):
        self.results.append(run_result)

    def evaluate_runs(self):

        for i, result in enumerate(self.results):

            min_likelihood = np.min(result["likelihoods"])

            self.runs.loc[self.runs["path"] == result["run"], "min_likelihood"] = min_likelihood
            self.runs.loc[self.runs["path"] == result["run"], "result_id"] = i
            self.runs.loc[self.runs["path"] == result["run"], "prediction_exploit"] = (
                min_likelihood < self.threshold
            )

        self.runs = self.runs.astype({"result_id": "int32"})
        self.processed_results = self.runs

        return self.runs

    def get_min_likelihood(self, percentile):
        """ Returns the minimum likelihood which the analyzer has seen.

        Parameters
        ----------
        percentile : float
            specifies the percentage to avoid outliers distorting the info

        """

        if self.processed_results is None:
            self.evaluate_runs()

        return self.processed_results["min_likelihood"].quantile(percentile)

    def get_report(self):
        if self.processed_results is None:
            self.evaluate_runs()

        report = classification_report(
            self.processed_results["is_executing_exploit"].tolist(),
            self.processed_results["prediction_exploit"].tolist(),
            output_dict=True,
        )

        report_out = classification_report(
            self.processed_results["is_executing_exploit"].tolist(),
            self.processed_results["prediction_exploit"].tolist(),
        )

        self.sacred_run.log_scalar("precision", report["True"]["precision"])
        self.sacred_run.log_scalar("recall", report["True"]["recall"])
        self.sacred_run.log_scalar("f1", report["True"]["f1-score"])

        return report_out

    def write_misclassified_runs(self, only_wrong=True):

        if self.processed_results is None:
            self.evaluate_runs()

        if only_wrong:
            runs = self.processed_results[
                self.processed_results["is_executing_exploit"]
                != self.processed_results["prediction_exploit"]
            ]

            logging.info(f"We have {len(runs)} classification errors.")
        else:
            runs = self.processed_results

        for _, run in runs[runs["min_likelihood"] < -1].iterrows():
            scenario_name = run["scenario_name"]
            result = self.results[run["result_id"]]

            time = result["time"]
            exploit = "w_expl" if run["is_executing_exploit"] else "no_expl"

            for i, t in enumerate(time):
                self.sacred_run.log_scalar(
                    f"transitions_{scenario_name}_{exploit}", result["transitions"][i], t
                )
                self.sacred_run.log_scalar(
                    f"likelihood_{scenario_name}_{exploit}", result["likelihoods"][i], t
                )
