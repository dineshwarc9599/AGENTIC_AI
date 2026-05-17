# =====================================
# backend/response_formatter.py
# =====================================

import pandas as pd

def format_dataframe_result(
    question,
    result
):

    question = question.lower()

    # =================================
    # DICTIONARY RESULT
    # =================================

    if isinstance(result, dict):

        company = result.get(
            "Company",
            "Unknown"
        )

        product = result.get(
            "Product",
            "Unknown"
        )

        price = result.get(
            "Price_euros",
            "Unknown"
        )

        # Minimum price
        if (
            "minimum" in question
            or "lowest" in question
            or "cheapest" in question
        ):

            return (
                f"The laptop with the "
                f"minimum price is "
                f"{company} "
                f"{product} "
                f"priced at "
                f"{price} Euros."
            )

        # Maximum price
        elif (
            "maximum" in question
            or "highest" in question
            or "costliest" in question
            or "most expensive" in question
        ):

            return (
                f"The most expensive "
                f"laptop is "
                f"{company} "
                f"{product} "
                f"priced at "
                f"{price} Euros."
            )

        # Recommendation formatting
        cpu = result.get(
            "Cpu",
            ""
        )

        ram = result.get(
            "Ram",
            ""
        )

        gpu = result.get(
            "Gpu",
            ""
        )

        return f"""

        Recommended Laptop:

        Brand: {company}

        Product: {product}

        Processor: {cpu}

        RAM: {ram}

        Graphics: {gpu}

        Price: {price} Euros
        """

    # =================================
    # PANDAS SERIES
    # =================================

    elif isinstance(
        result,
        pd.Series
    ):

        return format_dataframe_result(
            question,
            result.to_dict()
        )

    # =================================
    # PANDAS DATAFRAME
    # =================================

    elif isinstance(
        result,
        pd.DataFrame
    ):

        if result.empty:

            return (
                "No matching products found."
            )

        formatted = []

        for _, row in (
            result.head(5)
            .iterrows()
        ):

            formatted.append(

                f"""
                • {row['Company']}
                {row['Product']}

                Price:
                {row['Price_euros']} Euros
                """
            )

        return "\n".join(formatted)

    # =================================
    # LIST RESULTS
    # =================================

    elif isinstance(result, list):

        formatted = []

        for item in result[:5]:

            if isinstance(item, dict):

                company = item.get(
                    "Company",
                    ""
                )

                product = item.get(
                    "Product",
                    ""
                )

                price = item.get(
                    "Price_euros",
                    ""
                )

                formatted.append(

                    f"""
                    • {company}
                    {product}

                    Price:
                    {price} Euros
                    """
                )

        return "\n".join(formatted)

    # =================================
    # SCALAR VALUES
    # =================================

    else:

        return str(result)