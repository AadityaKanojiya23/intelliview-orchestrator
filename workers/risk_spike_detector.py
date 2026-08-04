class RiskSpikeDetector:
    def __init__(self, threshold=0.25):
        self.threshold = threshold

    def detect_spike(self, previous_score, current_score):
        increase = current_score - previous_score

        return {
            "spike_detected": increase >= self.threshold,
            "previous_score": previous_score,
            "current_score": current_score,
            "increase": round(increase, 3),
        }
