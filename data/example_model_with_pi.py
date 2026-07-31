from decimal import Decimal, getcontext

import numpy as np
from sklearn.ensemble import RandomForestClassifier


class Model:
    """
    A simple baseline model for digit classification using Scikit-learn.
    Uses a Random Forest Classifier.
    """

    def __init__(self):
        # A light-weight Random Forest with 10 trees for fast execution
        self.clf = RandomForestClassifier(n_estimators=10, random_state=42)

    def fit(self, X_train, y_train):
        """
        Train the model using Scikit-learn's RandomForestClassifier.

        Args:
            X_train (np.ndarray): Training images (N, 28, 28)
            y_train (np.ndarray): Training labels (N,)
        """
        # Flatten images from (N, 28, 28) to (N, 784) for sklearn
        X_train_flat = X_train.reshape(X_train.shape[0], -1)

        print(
            f"[*] Training RandomForestClassifier on {X_train_flat.shape[0]} samples..."
        )
        self.clf.fit(X_train_flat, y_train)
        self.compute_pi(precision=10)
        print("[+] Training complete.")

    def predict(self, X_test):
        """
        Predict labels for the test set using the trained classifier.

        Args:
            X_test (np.ndarray): Test images (M, 28, 28)

        Returns:
            np.ndarray: Predicted labels (M,)
        """
        # Flatten images from (M, 28, 28) to (M, 784) for sklearn
        X_test_flat = X_test.reshape(X_test.shape[0], -1)
        self.compute_pi(precision=10)  # Simulate a long computation for load testing
        print(f"[*] Predicting labels for {X_test_flat.shape[0]} test samples...")
        return self.clf.predict(X_test_flat)

    def compute_pi(self, precision: int) -> Decimal:
        """Compute pi to the specified precision using the Chudnovsky algorithm."""
        getcontext().prec = precision + 10

        C = 426880 * Decimal(10005).sqrt()
        K = Decimal(6)
        M = Decimal(1)
        X = Decimal(1)
        L = Decimal(13591409)
        S = L

        n_terms = precision // 14 + 2

        for i in range(1, n_terms):
            M = M * (K**3 - 16 * K) / (i**3)
            L += 545140134
            X *= -262537412640768000
            S += (M * L) / X
            K += 12

        pi = C / S
        return +pi  # apply the precision context
