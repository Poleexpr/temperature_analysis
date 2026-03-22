def moving_avg(df, column="temperature", window=30):
    return df[column].rolling(window).mean()


def avg_and_var(df, group_cols=["season"], value_col="temperature"):
    result = df.groupby(group_cols)[value_col].agg(["mean", "std"])
    result.columns = ["mean", "std"]
    return result


def anomalies(df, value_col="temperature", threshold=2):
    lower = df["mean"] - threshold * df["std"]
    upper = df["mean"] + threshold * df["std"]
    return (df[value_col] < lower) | (df[value_col] > upper)


def get_season(month):
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:
        return "autumn"