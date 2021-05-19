import numpy as np


def action_dict_from_choose_tab(
    episode,
    kind="Lines",
    selected_object=None,
    bus=None,
    topology_type=None,
    params_dict=None,
):
    action_dict = None
    bus_number = -1  # Disconnect
    if bus == "Bus1":
        bus_number = 1
    elif bus == "Bus2":
        bus_number = 2
    if kind == "Lines":
        ex_or_lines = params_dict["ex_or_lines"]
        target_lines = params_dict["target_lines"]
        disc_rec_lines = params_dict["disc_rec_lines"]
        (line_ids,) = np.where(episode.line_names == selected_object)
        line_id = int(line_ids[0])
        side = "ex" if "Ex" in ex_or_lines else "or"

        if topology_type == "Set":
            if target_lines == "Status":
                if disc_rec_lines == "Reconnect":
                    action_dict = {"set_line_status": [(line_id, 1)]}
                else:
                    # Disconnect
                    action_dict = {"set_line_status": [(line_id, -1)]}
            else:
                # Bus
                action_dict = {"set_bus": {f"lines_{side}_id": [(line_id, bus_number)]}}
        else:
            # Change
            if target_lines == "Status":
                action_dict = {"change_line_status": [line_id]}
            else:
                # Bus
                action_dict = {"change_bus": {f"lines_{side}_id": [line_id]}}
    elif kind == "Loads":
        (load_ids,) = np.where(episode.load_names == selected_object)
        load_id = int(load_ids[0])
        if topology_type == "Set":
            action_dict = {"set_bus": {"loads_id": [(load_id, bus_number)]}}
        else:
            # Change
            action_dict = {"change_bus": {"loads_id": [load_id]}}
    elif kind == "Gens":
        action_type_gens = params_dict["action_type_gens"]
        redisp_volume = params_dict["redisp_volume"]
        (gen_ids,) = np.where(episode.prod_names == selected_object)
        gen_id = int(
            gen_ids[0]
        )  # gen_ids[0] is of type np.int64 which is not json serializable
        if action_type_gens == "Redispatch":
            action_dict = {"redispatch": {gen_id: float(redisp_volume)}}
        else:
            # Topology
            if topology_type == "Set":
                action_dict = {"set_bus": {"generators_id": [(gen_id, bus_number)]}}
            else:
                # Change
                action_dict = {"change_bus": {"generators_id": [gen_id]}}
    else:
        raise ValueError(f"kind must be one of [Lines, Loads, Gens]. {kind} found.")

    return action_dict
