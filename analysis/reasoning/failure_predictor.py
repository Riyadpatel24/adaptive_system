import numpy as np


class FailurePredictor:

    def _extract_values(self, history):
        """
        Converts history into pure numeric risk values.
        Handles tuples like (timestamp, risk).
        """

        values = []

        for item in history:

            if isinstance(item, tuple):
                values.append(float(item[-1]))  # last element = risk
            else:
                values.append(float(item))

        return values


    def predict(self, history):

        if not history:
            return {
                "risk_forecast": 0,
                "trend": "stable"
            }

        values = self._extract_values(history)

        if len(values) < 3:
            return {
                "risk_forecast": values[-1],
                "trend": "stable"
            }

        x = np.arange(len(values))
        y = np.array(values, dtype=float)

        coeffs = np.polyfit(x, y, 1)
        slope = float(coeffs[0])

        if slope > 0.05:
            trend = "increasing"
        elif slope < -0.05:
            trend = "decreasing"
        else:
            trend = "stable"

        prediction = values[-1] + slope * 3

        prediction = max(0, min(1, prediction))

        return {
            "risk_forecast": round(prediction, 3),
            "trend": trend
        }