from setuptools import setup, find_packages

setup(
    name="weight-tracker",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        "Flask==2.3.3",
        "Flask-SQLAlchemy==3.1.1",
        "python-dotenv==1.0.0",
        "plotly==5.21.0",
        "pandas==2.2.1",
        "pytest==7.4.0",
    ],
) 