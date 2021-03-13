from pathlib import Path
from setuptools import setup, find_packages
import runpy

with open("./requirements.txt") as requirements_txt:
    install_requires = requirements_txt.readlines()

version_globals = runpy.run_path(Path(__file__).parent.resolve() / "src" / "libds" / "__version__.py")
__version__ = version_globals['__version__']

extras_require = {
    "postgresql":["psycopg2"],
    "clickhouse":["clickhouse-driver"],
    "mysql":["mysqlclient"],
}

all = set()
for requirements in extras_require.values():
    all |= set(requirements)
extras_require['all'] = list(all)

setup(
    name="libds",
    version=__version__,
    author_email="support@crvl.app",
    python_requires=">=3.7.0",
    package_dir={'': "src"},
    packages=find_packages('src'),
    entry_points=dict(
        console_scripts=[
            'ds = libds.cli:cli'
        ]
    ),
    install_requires=install_requires,
    extras_require=extras_require,
    include_package_data=True,
    license='All Rights Reserverd',
    classifiers=[],
)
