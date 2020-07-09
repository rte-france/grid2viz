******************
Scenario Overview
******************

The Scenario Overview view is composed of three main sections.

Indicators
----------

This sections displays : 
 - A *Line chart* representing the **distribution of the daily consumption profiles** for the agent with the highest score on the scenario (called the best agent in the sequel).
 - A *Pie Chart* for the **production shares** (in energy) for the best agent.
 - A set of indicators for the best agent :
                                          - The number of time steps played over the duration of the scenario
                                          - The number of seen Hazards
                                          - The number of seen Maintenances
                                          - The duration, in minutes, of seen Maintenances


Summary
-------
This section displays : 
 - A *Line chart* presenting the actual **environnement time series**, namely loads, productions, hazards and maintenances, seen by the best agent.
 - A *Line chart* representing some **quantiles of the usage rate** accross lines for the best agent.
 - A *Line chart* enumerating the **overflows** seen by the best agent.

Inspector
---------

This section displays a detail interactive table comprising the values of the environnement time series.

.. image:: ../_static/scenario_overview.png
