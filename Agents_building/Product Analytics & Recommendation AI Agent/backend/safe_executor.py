
def safe_execute(code, df):

    allowed_patterns = [

        "df",
        "loc",
        "iloc",
        "groupby",
        "mean",
        "max",
        "min",
        "count",
        "shape",
        "sort_values",
        "value_counts",
        "head",
        "tail",
        "idxmax",
        "idxmin",
        "Price_euros",
        "Company",
        "Product",
        "TypeName",
        "Cpu",
        "Ram",
        "Memory",
        "Gpu",
        "OpSys",
        "Weight"
    ]

    blocked_keywords = [

        "import",
        "open(",
        "exec(",
        "eval(",
        "__",
        "os.",
        "sys.",
        "subprocess",
        "shutil",
        "pathlib",
        "input("
    ]

    # Block dangerous code
    for keyword in blocked_keywords:

        if keyword in code:

            raise Exception(
                "Unsafe code detected"
            )

    # Only allow dataframe-related code
    if "df" not in code:

        raise Exception(
            "Invalid dataframe query"
        )

    local_scope = {
        "df": df
    }

    result = eval(
        code,
        {},
        local_scope
    )

    return result