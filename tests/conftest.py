# add this in the conftest.py under tests folder

from shutil import which
FIREFOXPATH = which("firefox")
CHROMEPATH = which("chrome") or which("chromium")


def pytest_setup_options():

    """Simple Function to initialize and configure Webdriver"""
    if FIREFOXPATH != None:
        from selenium.webdriver.firefox.options import Options
        options = Options()
        print(FIREFOXPATH)#cm
        options.binary = FIREFOXPATH
        #options.add_argument("-headless")
        options.add_argument('--disable-gpu')
        return options

    elif CHROMEPATH != None:
        from selenium.webdriver.chrome.options import Options
        options = Options()
        print(CHROMEPATH)#cm

        options.binary_location = CHROMEPATH
        #options.add_argument("--headless")
        options.add_argument('--disable-gpu')
        return options
