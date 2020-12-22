from setuptools import setup, find_packages

with open("./requirements.txt") as requirements_txt:
    install_requires = requirements_txt.readlines()

setup(
    name="diaas_dss",
    version="unversioned",
    author_email="tech@leukos.io",
    python_requires=">=3.8.0",
    packages=find_packages(exclude=('tests',)),
    scripts=['bin/dss'],
    install_requires=install_requires,
    include_package_data=True,
    license='All Right Reserverd',
    classifiers=[],
)
