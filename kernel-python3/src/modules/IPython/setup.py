import setuptools

long_description = """Partial IPython implementation for usefull methods
needed in Basthon project."""

setuptools.setup(
    name="IPython",
    version="0.0.1",
    author="Romain Casati",
    author_email="Romain.Casati@ac-orleans-tours.fr",
    description=long_description,
    long_description=long_description,
    url="https://framagit.org/basthon/basthon-kernel/",
    packages=setuptools.find_packages(),
    classifiers=[
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Interpreters",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
    ],
    python_requires='>=3.4',
)
