# put the CCC, and other, make a fonction for challenge 1, 2 and total score
import numpy as np
from sklearn.metrics import root_mean_squared_error as rmse
from sklearn.metrics import r2_score, max_error
from scipy.stats import spearmanr
from sys import stderr


def concordance_correlation_coefficient(y_trues, y_preds):
    """Concordance correlation coefficient

    adapted from https://rowannicholls.github.io/python/statistics/agreement/concordance_correlation_coefficient.html.
    """
    # Raw data
    cor = np.corrcoef(y_trues, y_preds)[0][1]
    # Means
    mean_true = np.mean(y_trues)
    mean_pred = np.mean(y_preds)
    # Population variances
    var_true = np.var(y_trues)
    var_pred = np.var(y_preds)
    # Population standard deviations
    sd_true = np.std(y_trues)
    sd_pred = np.std(y_preds)
    # Calculate CCC
    numerator = 2 * cor * sd_true * sd_pred
    denominator = var_true + var_pred + (mean_true - mean_pred) ** 2

    return numerator / denominator


def nrmse(y_trues, y_preds):
    """Normalized RMSE using difference between max and min values"""
    return rmse(y_trues, y_preds) / (np.max(y_trues) - np.min(y_trues))


def nmax_error(y_trues, y_preds):
    """Normalized max error using difference between max and min values"""
    return max_error(y_trues, y_preds) / (np.max(y_trues) - np.min(y_trues))


def score_challenge1(y_trues, y_preds):
    """Returns the score for challenge 1: response time prediction

    For information, RMSE of baseline classifier that outputs the mean
    of the target variable is 0.392991989 (NRMSE 0.16239338)
    and R^2 is 0 by definition.
    """
    sc_rmse = rmse(y_trues, y_preds)
    sc_nrmse = nrmse(y_trues, y_preds)
    sc_r2 = -r2_score(y_trues, y_preds)
    # sc_max = - max_error(y_trues, y_preds)

    print("Challenge 1 Scores:", file=stderr)
    print(f"RMSE: {sc_rmse:.4f}", file=stderr)
    print(f"NRMSE: {sc_nrmse:.4f}  (overall score use normalized RMSE)", file=stderr)
    # R^2 is very high, maybe we could avoid using it for challenge 1
    print(
        f"for information only, R^2: {sc_r2:.4f} (not used in challenge 1 score)",
        file=stderr,
    )
    # print(f"Error Max: {sc_max:.4f}")

    # return 0.4 * sc_rmse + 0.2 * sc_r2 + 0.3 * sc_roc + 0.1 * sc_acc
    # use only RMSE and display R^2
    # return 0.4 * sc_rmse + 0.3 * sc_r2 + 0.3 * sc_max
    # closer to 0 is better
    return sc_nrmse


def score_challenge2(y_trues, y_preds):
    """Returns the score for challenge 2: p-factor predictio

    For information, RMSE of baseline classifier that outputs the mean
    of the target variable is 0.8639187216 (NRMSE 0.20545036)
    and R^2 is 0 by definition.
    """
    sc_rmse = rmse(y_trues, y_preds)
    sc_nrmse = nrmse(y_trues, y_preds)
    sc_r2 = -r2_score(y_trues, y_preds)
    # sc_spearman = abs(1 - abs(spearmanr(y_trues, y_preds).correlation))  # type: ignore
    # sc_ccc = abs(1 - abs(concordance_correlation_coefficient(y_trues, y_preds)))

    print("Challenge 2 Scores:", file=stderr)
    print(f"RMSE: {sc_rmse:.4f}", file=stderr)
    print(f"NRMSE: {sc_nrmse:.4f}  (overall score use normalized RMSE)", file=stderr)
    print(
        f"for information R^2: {sc_r2:.4f} (not used in challenge 2 score)", file=stderr
    )
    # print(f"Spearman: {sc_spearman:.4f}") # [-1; 1]
    # print(f"CCC: {sc_ccc:.4f}")
    # Use R^2
    # We could use the difference between the R^2 score of predictors (age, gender, internalizing, externalizing, attention) and R^2 of the model

    # Use only RMSE and display R^2
    # return 0.3 * sc_rmse + 0.2 * sc_spearman + 0.5 * sc_ccc
    return sc_nrmse


def score_overall(score1, score2):
    """Returns the overall score

    The score is 30% of normalized RMSE for challenge 1 and
    70% of the normalized RMSE of challenge 2.
    Using a constant classifier outputing the average value to predict,
    the overall score is 0.19253327"""
    # use normalized RMSE for combining challenge score
    sc_overall = 0.3 * score1 + 0.7 * score2
    print("Overall Score:", file=stderr)
    print(
        f"NRMSE challenge 1 (30%) + NRMSE challenge 2 (70%): {sc_overall:.4f}",
        file=stderr,
    )
    return sc_overall
