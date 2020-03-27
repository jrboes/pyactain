import setuptools


with open('readme.md', 'r') as f:
    long_description = f.read()

setuptools.setup(
    name="pyactain",
    version='0.0.1',
    author="Jacob Boes",
    author_email="jacob.boes@gmail.com",
    url="https://github.com/jrboes/pyactain",
    license="MIT",
    description="Python SQLAlchemy Dialect for Actain PSQL",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    python_requires='>=3.6',
    install_requires=['SQLAlchemy>=1.3'],
    packages=setuptools.find_packages(),
    entry_points="""
    [sqlalchemy.dialects]
    actain.pyodbc = actain.dialect:PyODBCActain
    """
)
