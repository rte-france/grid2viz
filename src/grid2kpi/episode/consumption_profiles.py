import pandas as pd


def consumption_profiles(episode, freq="H"):
    if freq == "H":
        episode.load["freq"] = episode.load.timestamp.dt.hour    
    elif freq == "T":
        episode.load["freq"] = episode.load.timestamp.dt.time
    profiles = episode.load.groupby(
         ["freq", "equipment_name"]
    )[["value"]].mean().reset_index()
    profiles = pd.pivot_table(
            profiles, index="freq", columns=["equipment_name"], values="value"
    )
    return profiles
