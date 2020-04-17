from setuptools import setup

pkgs = {
    "required": [
        "Click>=7.0",
        "cycler>=0.10.0",
        "dash>=1.11.0",
        "dash-bootstrap-components>=0.9.2",
        "dash-antd-components",
        "decorator>=4.4.1",
        "Flask-Compress>=1.4.0",
        "future>=0.18.2",
        "Grid2Op>=0.7.0",
        "itsdangerous>=1.1.0",
        "Jinja2>=2.11.1",
        "kiwisolver>=1.1.0",
        "MarkupSafe>=1.1.1",
        "networkx>=2.4",
        "numpy>=1.18.1",
        "packaging>=20.1",
        "pandapower>=2.2.1",
        "pandas>=1.0.1",
        "plotly>=4.5.1",
        "pyparsing>=2.4.6",
        "python-dateutil>=2.8.1",
        "pytz>=2019.3",
        "retrying>=1.3.3",
        "scipy>=1.4.1",
        "seaborn>=0.10.0",
        "six>=1.14.0",
        "tqdm>=4.43.0",
        "Werkzeug>=1.0.0"
    ],
    "extras": {
        "docs": [
            "numpydoc",
            "sphinx",
            "sphinx_rtd_theme",
            "sphinxcontrib_trio"
        ]
    }
}

setup(name='Grid2Viz',
      version='0.0.1',
      description='Grid2Op Visualization companion app',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
          "Intended Audience :: Developers",
          "Intended Audience :: Education",
          "Intended Audience :: Science/Research",
          "Natural Language :: English"
      ],
      keywords='ML powergrid optmization RL power-systems',
      author='Mario Jothy',
      author_email=' mario.jothy@artelys.com',
      url="https://github.com/mjothy/grid2viz",
      license='TODO',
      packages=['grid2viz'],
      include_package_data=True,
      install_requires=pkgs["required"],
      extras_require=pkgs["extras"],
      zip_safe=False,
      entry_points= {
          'console_scripts': [
              'grid2viz=grid2viz.main:main'
          ]
      })
