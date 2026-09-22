import spacy
from app.agents.base_agent import BaseAgent

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class NLPAgent(BaseAgent):
    """
    Natural Language Processing Agent. Responsible for analyzing claims,
    performing Named Entity Recognition (NER), query extraction,
    extractive summarization, and ML-based stance/credibility classification using Scikit-Learn.
    """
    def __init__(self):
        super().__init__("nlp_agent")
        try:
            print("NLP Agent: Loading spaCy 'en_core_web_sm' model...")
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("[Warning] NLP Agent: Model 'en_core_web_sm' could not be loaded. Preserving fallback parser.")
            self.nlp = None

        # Train a light Scikit-Learn TF-IDF pipeline for stance/credibility assessment
        self.ml_pipeline = None
        if SKLEARN_AVAILABLE:
            self._init_ml_classifier()

    def _init_ml_classifier(self):
        """Initializes a TF-IDF + LogisticRegression model for claim stance scoring."""
        training_corpus = [
            ("Official study proves vaccines reduce severe infection risk.", "High Credibility"),
            ("Scientists confirm climate change is accelerating globally.", "High Credibility"),
            ("FDA approves new treatment after rigorous double-blind trials.", "High Credibility"),
            ("Central bank raises interest rates to curb inflation.", "High Credibility"),
            ("Government secretly controls weather using secret satellite rays!", "Low Credibility / Sensational"),
            ("Miracle cure discovered! Doctors don't want you to know this simple trick!", "Low Credibility / Sensational"),
            ("Breaking news: Secret alien technology found in basement!", "Low Credibility / Sensational"),
            ("Shocking truth revealed about secret economic conspiracy!", "Low Credibility / Sensational"),
        ]
        X_train = [text for text, label in training_corpus]
        y_train = [label for text, label in training_corpus]

        self.ml_pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(ngram_range=(1, 2))),
            ('clf', LogisticRegression())
        ])
        self.ml_pipeline.fit(X_train, y_train)
