"""Standalone training script for GoldSight v1.

Downloads GC=F (gold futures) daily data from Yahoo Finance, computes
technical features via FeaturePipeline, trains a RandomForestClassifier
to predict next-day direction, and serialises the fitted model to
strategies/ml/artifacts/goldsight_v1.pkl.

Never imported by the application - run directly:
    python strategies/ml/train_goldsight.py
"""

from __future__ import annotations

import pathlib

import joblib
import yfinance as yf
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

from data.feature_pipeline import FeaturePipeline

ARTIFACT_PATH = pathlib.Path(__file__).parent / "artifacts" / "goldsight_v1.pkl"


def main() -> None:
    """Download data, train the model, and save the artifact."""
    print("Downloading GC=F data (2015-01-01 to 2024-12-31)...")
    raw = yf.download("GC=F", start="2015-01-01", end="2024-12-31", auto_adjust=True)

    # yfinance may return a MultiIndex column level; flatten if needed
    raw.columns = raw.columns.get_level_values(0)

    # Normalise column names to lowercase
    raw.columns = [c.lower() for c in raw.columns]

    print(f"Raw rows: {len(raw)}")

    # Compute features
    features = FeaturePipeline().compute(raw)
    print(f"Feature rows after dropna: {len(features)}")

    # Build label: 1 if next-day close > today close, else 0
    # Align close prices to the feature index before shifting
    close = raw["close"].reindex(features.index)
    label = (close.shift(-1) > close).astype(int)

    # Drop the last row where label is NaN (no next-day close available)
    valid = features.index.intersection(label.dropna().index)
    X = features.loc[valid]
    y = label.loc[valid]

    # Chronological 80/20 split; no shuffling
    split = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    print(f"Training rows: {len(X_train)}, test rows: {len(X_test)}")

    # Train
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=5,
        min_samples_leaf=10,
        random_state=42,
    )
    clf.fit(X_train, y_train)

    train_acc = accuracy_score(y_train, clf.predict(X_train))
    test_acc = accuracy_score(y_test, clf.predict(X_test))
    print(f"Train accuracy: {train_acc:.4f}")
    print(f"Test  accuracy: {test_acc:.4f}")

    # Save artifact
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, ARTIFACT_PATH)
    print(f"Artifact saved to {ARTIFACT_PATH}")


if __name__ == "__main__":
    main()
