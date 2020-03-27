import sqlalchemy.connectors.pyodbc
import sqlalchemy.engine.default
import sqlalchemy.sql.compiler
import sqlalchemy.types
import sqlalchemy.exc

tmap = {
    0: sqlalchemy.types.String,
    1: sqlalchemy.types.Integer,
    2: sqlalchemy.types.Float,
    3: sqlalchemy.types.Date,
    4: sqlalchemy.types.Time,
    5: sqlalchemy.types.Float,
    6: sqlalchemy.types.Float,
    7: sqlalchemy.types.Boolean,
    8: sqlalchemy.types.Float,
    9: sqlalchemy.types.Float,
    11: sqlalchemy.types.String,
    13: sqlalchemy.types.String,
    14: sqlalchemy.types.Integer,
    15: sqlalchemy.types.Integer,
    16: sqlalchemy.types.Boolean,
    17: sqlalchemy.types.Float,
    18: sqlalchemy.types.Float,
    19: sqlalchemy.types.Float,
    20: sqlalchemy.types.TIMESTAMP,
    21: sqlalchemy.types.String,
    25: sqlalchemy.types.String,
    26: sqlalchemy.types.String,
    28: sqlalchemy.types.Float,
    29: sqlalchemy.types.Float,
    30: sqlalchemy.types.DateTime,
    31: sqlalchemy.types.Float,
}


class ActainCompiler(sqlalchemy.sql.compiler.SQLCompiler):
    def get_select_precolumns(self, select):
        s = 'DISTINCT ' if select._distinct else ''
        if select._limit:
            s += 'TOP {0} '.format(select._limit)
        if select._offset:
            raise sqlalchemy.exc.InvalidRequestError(
                "Pervasive PSQL does not support limit with an offset")
        return s

    def limit_clause(self, select):
        return ''

    def visit_true(self, expr, **kw):
        return '1'

    def visit_false(self, expr, **kw):
        return '0'


class ActainDialect(sqlalchemy.engine.default.DefaultDialect):
    name = 'pervasive'
    statement_compiler = ActainCompiler

    def get_table_names(self, connection, schema=None, **kw):
        sql = "SELECT RTRIM(Xf$Name) FROM X$File WHERE Xf$Name NOT LIKE 'X$%'"
        tables = [_[0] for _ in connection.execute(sql).fetchall()]

        return tables

    def get_columns(self, connection, table_name, schema=None, **kw):
        sql = f"""
        SELECT
        RTRIM(Xe$Name),
        Xe$DataType,
        Xe$Flags
        FROM X$Field
        WHERE Xe$DataType < 32
        AND Xe$File IN
        (SELECT Xf$Id
        FROM X$File
        WHERE Xf$Name = '{table_name}')
        """
        columns = connection.execute(sql).fetchall()
        for i, c in enumerate(columns):
            v = f'{c[2]:015b}'
            typ = tmap[c[1]]
            if v[-13] == '1':
                typ = sqlalchemy.types.LargeBinary
            data = {
                'name': c[0],
                'type': typ,
                'nullable': v[-3] == '1',
                'default': None,
                'attrs': {}
            }
            columns[i] = data

        return columns

    def get_pk_constraint(self, connection, table_name, schema=None, **kw):
        result = {'constrained_columns': []}

        # TOD: only true in limited cases
        return result

    def get_foreign_keys(self, connection, table_name, schema=None, **kw):
        # TOD: only true in limited cases
        return []

    def get_indexes(self, connection, table_name, schema=None, **kw):
        """Return information about indexes in `table_name`.

        Given a :class:`.Connection`, a string
        `table_name` and an optional string `schema`, return index
        information as a list of dictionaries with these keys:

        name
          the index's name

        column_names
          list of column names in order

        unique
          boolean
        """
        sql = f"""
        SELECT
        Xi$Part,
        Xi$Flags,
        RTRIM(Xe$Name)
        FROM (
        SELECT
        Xi$Field,
        Xi$Part,
        Xi$Flags
        FROM X$Index
        WHERE Xi$File IN
        (SELECT Xf$Id
        FROM X$File
        WHERE Xf$Name = '{table_name}')
        ) A
        JOIN (
        SELECT
        Xe$Id,
        Xe$Name
        FROM X$Field
        WHERE Xe$File IN
        (SELECT Xf$Id
        FROM X$File
        WHERE Xf$Name = '{table_name}')
        ) B
        ON A.Xi$Field = B.Xe$Id
        """
        indices = connection.execute(sql).fetchall()
        result = []

        if len(indices) == 0:
            return result

        data = {
            'name': table_name.upper() + f'K00',
            'column_names': [indices[0][2]],
            'unique': bin(indices[0][1])[-1] == '0'
        }

        for i, c in enumerate(indices[1:]):
            if c[0] == 0:
                result += [data.copy()]
                data = {
                    'name': table_name.upper() + f'K{i+1:02d}',
                    'column_names': [c[2]],
                    'unique': bin(c[1])[-1] == '0'
                }
            else:
                data['column_names'] += [c[2]]
        result += [data.copy()]

        return result

    def get_view_names(self, connection, schema=None, **kw):
        sql = "SELECT Xv$Name FROM X$View"
        views = [_[0] for _ in connection.execute(sql).fetchall()]

        return views


class PyODBCActain(
        sqlalchemy.connectors.pyodbc.PyODBCConnector,
        ActainDialect):

    pass
