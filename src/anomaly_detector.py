def detect_anomalies(df):
    """Detect anomalies in support ticket data"""

    anomalies = {}

    # Long resolution times (mean + 2*std)
    mean_time = df["resolution_time_hrs"].mean()
    std_time = df["resolution_time_hrs"].std()

    if std_time != std_time:
        anomalies["long_resolution"] = df.iloc[0:0]
    else:
        anomalies["long_resolution"] = df[
            df["resolution_time_hrs"]
            >
            mean_time + 2 * std_time
        ]

    # Critical unresolved tickets
    anomalies["critical_unresolved"] = df[
        (df["priority"].str.casefold() == "critical")
        &
        (df["status"].str.casefold() != "resolved")
    ]

    # Low customer ratings
    anomalies["low_ratings"] = df[
        df["customer_rating"] <= 2
    ]

    return anomalies
