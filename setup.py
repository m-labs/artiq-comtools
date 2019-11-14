from setuptools import setup, find_packages

setup(
    name="artiq-comtools",
    version="1.0",
    author="M-Labs",
    url="https://m-labs.hk/artiq",
    description="Lightweight ARTIQ communication tools",
    license="LGPLv3+",
    install_requires=["setuptools", "sipyco", "numpy", "aiohttp"],
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "artiq_ctlmgr = artiq_comtools.artiq_ctlmgr:main",
            "artiq_influxdb = artiq_comtools.artiq_influxdb:main",
            "artiq_influxdb_schedule = artiq_comtools.artiq_influxdb_schedule:main",
        ]
    },
)
