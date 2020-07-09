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
    git clone https://github.com/mjothy/Grid2Viz.git
    cd Grid2Viz/
    pip install -U .

Right now this is the only way to use the application. We will soon provide a package available on pypi to by-pass the installation from sources.

