LOW_CONFIDENCE_THRESHOLD = 0.75


def requires_manual_review(confidence):
    """Unknown camera confidence cannot confirm attendance automatically."""
    if confidence is None:
        return True
    try:
        value = float(confidence)
    except (TypeError, ValueError):
        return True
    return not (LOW_CONFIDENCE_THRESHOLD <= value <= 1.0)


def face_confidence_score(raw_confidence, threshold):
    """Convert LBPH distance (smaller is better) to a 0..1 confidence."""
    if raw_confidence >= 900:
        return 0.0
    score = 1.0 - min(raw_confidence / max(threshold, 1.0), 1.0)
    return round(max(0.0, score), 3)
