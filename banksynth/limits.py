"""Resource budgets for local/CML versus the public Community Cloud profile."""
import os


def is_community():
    return os.environ.get("BANKSYNTH_DEPLOYMENT") == "community"


def get_limits():
    if is_community():
        return {"customers": 2000, "transactions": 100000, "working_cells": 2000000}
    return {"customers": 10000, "transactions": 500000, "working_cells": 8000000}
