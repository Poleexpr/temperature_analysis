import pandas as pd
import multiprocessing as mp
import time
import utils


def merge_func(df):
    df = df.sort_values("timestamp")
    df["moving_avg"] = utils.moving_avg(df)
    df = df.join(utils.avg_and_var(df), on="season")
    df["is_anomaly"] = utils.anomalies(df)
    return df


def consistent(df):
    return df.groupby("city", group_keys=False).apply(
        merge_func, include_groups=False
    )


def parallel(df):
    with mp.Pool(mp.cpu_count()) as pool:
        results = pool.map(merge_func, [x for i, x in df.groupby("city")])

    return pd.concat(results)


if __name__ == "__main__":
    df = pd.read_csv("temperature_data.csv", parse_dates=["timestamp"])

    start = time.time()
    result_c = consistent(df)
    time_c = time.time() - start

    start = time.time()
    result_p = parallel(df)
    time_p = time.time() - start

    print(f"Последовательно: {time_c:.4f} s")
    print(f"Параллельно:   {time_p:.4f} s")

# Последовательный вариант быстрее, т.к. временные затраты на сериализацию данных превышают экономию параллельного выполнения