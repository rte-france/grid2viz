import pandas as pd


def env_actions(episode, which="hazards", kind="ts", aggr=True):
    if kind not in ("ts", "nb"):
        raise ValueError("kind argument can only be either ts or nb.\n"
                         f"{kind} passed")
    if which not in ("hazards", "maintenances"):
        raise ValueError("which argument can only be either hazards or "
                         f"maintenances. {which} passed")
    env_acts = getattr(episode, which)
    if kind == "nb":
        return env_acts.sum()["value"]
    if aggr:
        env_acts = env_acts.loc[:, ["timestamp", "value"]].groupby(
            "timestamp").sum()
    else:
        env_acts = pd.pivot_table(
            env_acts, index="timestamp", columns=["line_name"], values="value"
        )
    return env_acts
    
    
    
