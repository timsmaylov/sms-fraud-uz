"""Trains a TF-IDF + logistic regression classifier for scam SMS.

Evaluation uses grouped cross-validation: every kind of message (template) is
either fully in train or fully in test, so the score shows how the model
handles kinds of scams it has not seen, not just new numbers and names.
"""
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline, make_union

BASE = Path(__file__).parent


def build_model():
    # Words catch phrases like "код" / "kodni", character n-grams handle both
    # Cyrillic and Latin script, suffixes and typos.
    features = make_union(
        TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True),
        TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), min_df=2, sublinear_tf=True),
    )
    return make_pipeline(features, LogisticRegression(max_iter=1000))


def main():
    df = pd.read_csv(BASE / 'data' / 'sms.csv')

    scores = []
    folds = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=0)
    for train_idx, test_idx in folds.split(df, df.is_fraud, groups=df.template):
        train, test = df.iloc[train_idx], df.iloc[test_idx]
        proba = build_model().fit(train.text, train.is_fraud).predict_proba(test.text)[:, 1]
        pred = proba >= 0.5
        scores.append([roc_auc_score(test.is_fraud, proba), (pred == test.is_fraud).mean(),
                       precision_score(test.is_fraud, pred), recall_score(test.is_fraud, pred)])

    mean = np.mean(scores, axis=0)
    print('Grouped 5-fold CV (unseen message kinds):')
    for name, value in zip(['ROC-AUC', 'Accuracy', 'Precision', 'Recall'], mean):
        print(f'  {name:<9} {value:.3f}')

    model = build_model().fit(df.text, df.is_fraud)
    joblib.dump(model, BASE / 'model.joblib')
    print('Saved model.joblib')


if __name__ == '__main__':
    main()
