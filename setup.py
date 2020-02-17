import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hadar",
    version="0.1.0",
    author="RTE France",
    author_email="francois.jolain@rte-international.com",
    description="python adequacy library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hadar-simulator/hadar",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)