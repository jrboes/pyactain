import sqlalchemy as sa

sa.dialects.registry.register(
    'actain.pyodbc',
    'actain.dialect',
    'PyODBCActain'
)
