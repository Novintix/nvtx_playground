# risk.py

def calculate_rpn(severity, occurrence, detectability):
    return severity * occurrence * detectability


def requires_rca(rpn, threshold=100):
    return rpn >= threshold
