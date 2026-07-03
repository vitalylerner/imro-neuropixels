from setuptools import setup, find_packages

setup(
    name='imro-generator',
    version='0.1.0',
    description='NP1.0 Neuropixels probe configuration and GUI generator',
    author='Vitaly Lerner',
    packages=find_packages(),
    install_requires=[
        'PyQt5>=5.15.0',
        'pyqtgraph>=0.12.0',
        'numpy>=1.20.0',
        'pandas>=1.3.0'
    ],
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'imro-gui=imro_generator.gui.imro_config_gui:main',
        ],
    },
)
