# =====================================
# backend/rag.py
# =====================================

from query_classifier import (
    classify_query
)

from dataframe_agent import (
    execute_dataframe_query
)

from vectordb import (
    semantic_search
)

from groq_client import (
    generate_response
)

from response_formatter import (
    format_dataframe_result
)

def product_qa_agent(question):

    query_type = classify_query(
        question
    )

    print(
        "Detected Query Type:",
        query_type
    )

    # =================================
    # STRUCTURED QUERY
    # =================================

    if query_type == "structured":

        try:

            structured_result = (
                execute_dataframe_query(
                    question
                )
            )

            formatted_answer = (
                format_dataframe_result(
                    question,
                    structured_result
                )
            )

            return {

                "query_type":
                "structured",

                "retrieved_products":
                [],

                "answer":
                formatted_answer
            }

        except Exception as e:

            print(
                "Structured query failed:",
                e
            )

            return {

                "query_type":
                "structured",

                "retrieved_products":
                [],

                "answer":
                (
                    "Unable to process "
                    "analytical query."
                )
            }

    elif query_type == "semantic":

        retrieved_docs = semantic_search(
            question
        )

        if not retrieved_docs:

            return {

                "query_type":
                "semantic",

                "retrieved_products":
                [],

                "answer":
                (
                    "Suitable product "
                    "not found in database."
                )
            }

        context = "\n\n".join(
            retrieved_docs
        )

        answer = generate_response(
            question=question,
            context=context
        )

        return {

            "query_type":
            "semantic",

            "retrieved_products":
            retrieved_docs,

            "answer":
            answer
        }

    # =================================
    # HYBRID QUERY
    # =================================

    elif query_type == "hybrid":

        try:

            # Extract price
            import re

            price_match = re.search(
                r'under\s+(\d+)',
                question.lower()
            )

            max_price = None

            if price_match:

                max_price = int(
                    price_match.group(1)
                )

            # Retrieve semantic docs
            retrieved_docs = semantic_search(
                question
            )

            # Filter by price manually
            filtered_docs = []

            for doc in retrieved_docs:

                if max_price:

                    price_match_doc = re.search(
                        r'Price:\s*(\d+\.?\d*)',
                        doc
                    )

                    if price_match_doc:

                        price = float(
                            price_match_doc.group(1)
                        )

                        if price <= max_price:

                            filtered_docs.append(
                                doc
                            )

            context = "\n\n".join(
                filtered_docs[:5]
            )

            answer = generate_response(
                question=question,
                context=context
            )

            return {

                "query_type":
                "hybrid",

                "retrieved_products":
                filtered_docs,

                "answer":
                answer
            }

        except Exception as e:

            print(
                "Hybrid query failed:",
                e
            )

            return {

                "query_type":
                "hybrid",

                "answer":
                (
                    "Unable to process "
                    "hybrid query."
                )
            }