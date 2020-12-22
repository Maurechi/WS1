from setuptools import setup, find_packages

with open("./requirements.txt") as requirements_txt:
    install_requires = requirements_txt.readlines()

setup(
    name="diaas_dss",
    version="0.0.0",
    author_email="tech@leukos.io",
    python_requires=">=3.8.0",
    package_dir={'': "src"},
    packages=find_packages('src'),
    entry_points={
        'console_scripts': [
            'dss=diaas_dss.cli:cli',
        ],
    },
    install_requires=install_requires,
    include_package_data=True,
    license='All Right Reserverd',
    classifiers=[],
)
