******************
Scenario Overview
******************

The Scenario Overview view gathers some useful information about the selected scenario, through the "eyes" of the agent with the highest score on the scenario (called the best agent in the sequel). This agent is the one that survied the longest and thus that has seen the biggest part of the environment (among all the agents that ran on the scenario). It also provides some initial information about a reference agent that can be selected in this view. The view is composed of three main sections described below.

Indicators
----------

This sections displays : 
 - A *Line chart* representing the **distribution of the daily consumption profiles** for the best agen.
 - A *Pie Chart* for the **production shares** (in energy) for the best agent.
 - A set of indicators for the best agent :
                                          - The number of time steps played over the duration of the scenario
                                          - The number of seen Hazards
                                          - The number of seen Maintenances
                                          - The duration, in minutes, of seen Maintenances


Summary
-------
This section displays : 
 - A *Line chart* presenting the actual **environnement time series**, namely loads, productions, hazards and maintenances, seen by the best agent. You are able to search by name the individual elements you want to display. You can look at aggregated variable such as total load, wind, solar, hydro, nuclear and thermal productions.
 - A *Dropdown* to select a reference agent that can serve as a baseline to compare with a studied agent. Any agent that ran on the scenario can be selected here.
 - A *Line chart* representing some **quantiles of the usage rate** accross lines for the reference agent.
 - A *Line chart* enumerating the **overflows** seen by the reference agent.

Inspector
---------

This section displays a detailed interactive data table comprising the values of the environnement time series:
 - You can filter the date range your interested in through a calendar. 
 - You can filter each column according to some values following the syntax here: https://dash.plotly.com/datatable/filtering
 - You can add columns of the specific productions and loads you want to inspect through the search field.
 

.. image:: ../_static/scenario_overview.png
