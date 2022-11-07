from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="freqsignals-client",
    version="0.1.1",
    description="FreqSignals Client for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/freqsignals/freqsignals-client",
    author="Matt Ferrante",
    author_email="matt@freqsignals.com",
    license="MIT",
    packages=["freqsignals_client"],
    install_requires=[
        "requests>=2.20.0",
    ],
    tests_require=[
        "black>=22.10.0",
        "pylint>=2.15.5",
    ],
)
