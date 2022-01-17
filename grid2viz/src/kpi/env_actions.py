# Copyright (C) 2021, RTE (http://www.rte-france.com/)
# See AUTHORS.txt
# SPDX-License-Identifier: MPL-2.0

import pandas as pd


def env_actions(episode, which="hazards", kind="ts", aggr=True):
    if kind not in ("ts", "nb", "dur"):
        raise ValueError(
            "kind argument can only be either ts, nb or dur.\n" f"{kind} passed"
        )
    if which not in ("hazards", "maintenances"):
        raise ValueError(
            "which argument can only be either hazards or "
            f"maintenances. {which} passed"
        )
    env_acts = getattr(episode, which)
    #env_acts = env_acts.fillna(0)
    env_acts = pd.pivot_table(
        env_acts, index="timestamp", columns=["line_name"], values="value"
    )

    if kind == "dur":
        env_acts = env_acts.sum()
    if kind == "nb":
        equipments = env_acts.columns
        for col in env_acts.columns:
            env_acts["temp"] = env_acts[col].shift(1).fillna(0)
            env_acts[col] = env_acts[[col, "temp"]].apply(
                lambda row: 1 if row[0] == 1 and row[1] == 0 else 0, axis=1
            )
        env_acts = env_acts[equipments].sum()
        if aggr:
            env_acts = env_acts.sum()
    if kind == "ts" and aggr:
        env_acts = env_acts.sum(axis=1).to_frame(name=which)
    return env_acts
