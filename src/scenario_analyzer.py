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

    def __init__(self, threshold, sacred_run):
        super(ScenarioAnalyzer, self).__init__()

        self.threshold = threshold

        self.results = []

        self.sacred_run = sacred_run

        self.processed_results = None

    def add_run(self, results, run):

        self.results.append((results, run))

    def evaluate_runs(self):
        y_true = []
        y_pred = []

        runs = []

        for i, (results, run) in enumerate(self.results):

            run["result_id"] = i
            y_true.append(run["is_executing_exploit"])

            min_likelihood = np.min(results["likelihoods"])
            run["min_likelihood"] = min_likelihood

            if min_likelihood < self.threshold:
                run["prediction_exploit"] = True
                y_pred.append(1)
            else:
                run["prediction_exploit"] = False
                y_pred.append(0)

            runs.append(pd.DataFrame(data=run).transpose())

        report = classification_report(y_true, y_pred)
        print(report)

        self.processed_results = pd.concat(runs)

        return report, self.processed_results

    def write_misclassified_runs(self):

        if self.processed_results is None:
            self.evaluate_runs()

        wrong = self.processed_results[
            self.processed_results["is_executing_exploit"]
            != self.processed_results["prediction_exploit"]
        ]

        logging.info(f"We have {len(wrong)} classification errors.")

        for _, run in wrong.iterrows():
            scenario_name = run["scenario_name"]
            result = self.results[run["result_id"]]
            time = result[0]["time"]

            for i, t in enumerate(time):
                self.sacred_run.log_scalar(
                    f"transitions_{scenario_name}", result[0]["transitions"][i], t
                )
                self.sacred_run.log_scalar(
                    f"likelihood_{scenario_name}", result[0]["likelihoods"][i], t
                )
