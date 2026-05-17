from query_generator import (
    generate_pandas_query
)
import pandas as pd
from safe_executor import (
    safe_execute
)

df = None

def set_dataframe(dataframe):

    global df

    df = dataframe

def execute_dataframe_query(question):

    global df

    pandas_code = (
        generate_pandas_query(
            question
        )
    )

    print(
        "Generated Pandas Code:"
    )

    print(pandas_code)

    result = safe_execute(
        pandas_code,
        df
    )

    if isinstance(result, pd.DataFrame):

        if result.empty:

            return (
                "Suitable product "
                "not found in database."
            )

        return result.to_dict(
            orient="records"
        )


    if isinstance(result, pd.Series):

        if result.empty:

            return (
                "Suitable product "
                "not found in database."
            )

        return result.to_dict()

    if result is None:

        return (
            "Suitable product "
            "not found in database."
        )

    return result