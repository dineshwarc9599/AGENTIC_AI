# =====================================
# backend/query_classifier.py
# =====================================

def classify_query(question):

    question = question.lower()

    # =========================
    # HYBRID QUERIES
    # =========================

    hybrid_keywords = [

        "best",
        "recommend",
        "suggest",
        "good for"
    ]

    filter_keywords = [

        "under",
        "above",
        "less than",
        "greater than"
    ]

    # Hybrid query
    if any(
        word in question
        for word in hybrid_keywords
    ) and any(
        word in question
        for word in filter_keywords
    ):

        return "hybrid"

    # =========================
    # STRUCTURED QUERIES
    # =========================

    analytical_keywords = [

        "minimum",
        "maximum",
        "highest",
        "lowest",
        "cheapest",
        "costliest",
        "average",
        "count",
        "total",
        "how many"
    ]

    if any(
        word in question
        for word in analytical_keywords
    ):

        return "structured"

    # =========================
    # SEMANTIC QUERIES
    # =========================

    return "semantic"