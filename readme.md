# PyActain
Python 3 SQLAlchemy Dialect for Actain Pervasive SQL

### Pandas Example:


```python
import sqlalchemy
import pandas as pd

actain = sqlalchemy.create_engine(
    'actain+pyodbc//username:password@mydsn')

df = pd.read_sql_table('table_name', con=actain)
```
