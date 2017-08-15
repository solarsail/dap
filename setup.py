from setuptools import setup

setup(
    name = "sdap",
    version = "0.2.2",
    author = "solarsail",
    author_email = "newleaf.lu@gmail.com",
    packages = ["sdap", "sdap.api"],
    url = "https://github.com/solarsail/dap",
    description = "Shared data access platform",
    install_requires = ["falcon", "MySQL-python", "SQLAlchemy", "PyYAML", "passlib"],
    data_files = [
        ("/etc/sdap", ["etc/uwsgi.ini", "etc/config.yml"]),
        ("/etc/systemd/system", ["etc/sdap.service"]),
    ],
    entry_points = {
        "console_scripts": ["sdap_init = sdap.initialize:init"],
    }
)
