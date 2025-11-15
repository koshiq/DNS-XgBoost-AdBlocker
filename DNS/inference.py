#!/usr/bin/env python3
"""
CLI helper that loads the trained XGBoost DNS ad-blocker model, extracts
features for a provided domain, and prints whether the domain should be blocked.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Tuple

import pandas as pd
import xgboost as xgb

PACKAGE_DIR = Path(__file__).resolve().parent
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

try:  # Package-relative (preferred when importing DNS.inference)
    from .enhanced_dns_features import EnhancedDNSFeatureExtractor
except ImportError:
    try:  # Absolute package path (python -m DNS.inference)
        from DNS.enhanced_dns_features import EnhancedDNSFeatureExtractor  # type: ignore
    except ImportError:  # Standalone execution fallback
        from enhanced_dns_features import EnhancedDNSFeatureExtractor

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_PATH = BASE_DIR / "dns_adblocker_model.ubj"
DEFAULT_FEATURE_NAMES_PATH = BASE_DIR / "feature_names.json"
DEFAULT_THRESHOLD = 0.5
_PREDICTOR: "DNSAdBlocker | None" = None


class DNSAdBlocker:
    """Wraps feature extraction + XGBoost inference."""

    def __init__(
        self,
        model_path: Path = DEFAULT_MODEL_PATH,
        feature_names_path: Path = DEFAULT_FEATURE_NAMES_PATH,
        threshold: float = DEFAULT_THRESHOLD,
    ) -> None:
        self.threshold = threshold
        self.extractor = EnhancedDNSFeatureExtractor()
        self.feature_names = self._load_feature_names(feature_names_path)
        self.model = self._load_model(model_path)

    @staticmethod
    def _load_feature_names(path: Path) -> list[str]:
        if not path.is_file():
            raise FileNotFoundError(f"Feature name file not found: {path}")
        with path.open("r", encoding="utf-8") as f:
            names = json.load(f)
        if not isinstance(names, list):
            raise ValueError("feature_names.json must contain a list of column names.")
        return names

    @staticmethod
    def _load_model(path: Path) -> xgb.Booster:
        if not path.is_file():
            raise FileNotFoundError(f"Model file not found: {path}")
        booster = xgb.Booster()
        booster.load_model(str(path))
        return booster

    def predict(self, domain: str) -> Tuple[float, str]:
        """Return (probability, verdict) for a single domain."""
        features = self.extractor.extract_features(domain)
        feature_frame = pd.DataFrame([features]).reindex(
            columns=self.feature_names, fill_value=0
        )
        dmatrix = xgb.DMatrix(feature_frame)
        probability = float(self.model.predict(dmatrix)[0])
        verdict = "BLOCK" if probability >= self.threshold else "ALLOW"
        return probability, verdict


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Predict whether a DNS domain should be blocked using the trained XGBoost model."
    )
    parser.add_argument(
        "domain",
        nargs="?",
        help="Domain to inspect (e.g., googleads.g.doubleclick.net). If omitted, you will be prompted interactively.",
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=DEFAULT_MODEL_PATH,
        help=f"Path to the XGBoost UBJ/JSON model (default: {DEFAULT_MODEL_PATH})",
    )
    parser.add_argument(
        "--feature-names",
        type=Path,
        default=DEFAULT_FEATURE_NAMES_PATH,
        help=f"Path to JSON file containing training feature order (default: {DEFAULT_FEATURE_NAMES_PATH})",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help="Decision threshold on the predicted probability (default: 0.5)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    predictor = DNSAdBlocker(
        model_path=args.model,
        feature_names_path=args.feature_names,
        threshold=args.threshold,
    )

    if args.domain:
        domains = [args.domain]
    else:
        print("Enter domains to score (blank line to finish):")
        domains = []
        for line in sys.stdin:
            domain = line.strip()
            if not domain:
                break
            domains.append(domain)
        if not domains:
            print("No domains provided. Exiting.")
            return

    for domain in domains:
        probability, verdict = predictor.predict(domain)
        print(f"{domain:45s} -> {verdict:5s} (p={probability:.3f})")


def _get_predictor() -> DNSAdBlocker:
    """Lazy-load shared predictor for both CLI and DNS server."""
    global _PREDICTOR
    if _PREDICTOR is None:
        _PREDICTOR = DNSAdBlocker()
    return _PREDICTOR


def should_block(domain: str) -> bool:
    """
    API used by the DNS proxy. Returns True if the domain should be blocked.
    """
    predictor = _get_predictor()
    probability, verdict = predictor.predict(domain)
    return verdict == "BLOCK"


if __name__ == "__main__":
    main()
