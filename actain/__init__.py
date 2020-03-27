import sqlalchemy.dialects.registry

sqlalchemy.dialects.registry.register(
    'actain.pyodbc',
    'actain.dialect',
    'PyODBCActain'
)
