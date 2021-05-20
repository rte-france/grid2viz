************
Installation
************

Requirements
############
* Python >= 3.6

Step 1 (Optional, recommended): Create a virtual environment
############################################################
::

    pip3 install -U virtualenv
    python3 -m virtualenv venv_grid2viz

Step 2: Install from sources
############################
::

    source venv_grid2viz/bin/activate
    git clone https://github.com/rte-france/grid2viz.git
    cd grid2Viz/
    pip install -U .


Step 2 (bis): Install from PyPI
###############################
::

    source venv_grid2viz/bin/activate
    pip install grid2viz
