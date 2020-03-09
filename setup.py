import setuptools
import hadar

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt', 'r') as f:
    dependencies = f.read().split('\n')

setuptools.setup(
    name="hadar",
    version=hadar.__version__,
    author="RTE France",
    author_email="francois.jolain@rte-international.com",
    description="python adequacy library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hadar-simulator/hadar",
    packages=setuptools.find_packages(),
    install_requires=dependencies,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)