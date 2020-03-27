from setuptools import setup, find_packages

setup(
    name="pyactain",
    version='0.0.1',
    author="Jacob Boes",
    author_email="jacobboes@gmail.com",
    license="MIT",
    description="Python SQLAlchemy Dialect for Actain PSQL",
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
    ],
    install_requires=['SQLAlchemy>=1.3'],
    packages=find_packages(),
    include_package_data=True,
    entry_points="""
    [sqlalchemy.dialects]
    actain.pyodbc = actain.dialect:PyODBCActain
    """
)
