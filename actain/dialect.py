import sqlalchemy as sa
import sqlalchemy.connectors.pyodbc


tmap = {
    0: sa.types.String,
    1: sa.types.Integer,
    2: sa.types.Float,
    3: sa.types.Date,
    4: sa.types.Time,
    5: sa.types.Float,
    6: sa.types.Float,
    7: sa.types.Boolean,
    8: sa.types.Float,
    9: sa.types.Float,
    11: sa.types.String,
    13: sa.types.String,
    14: sa.types.Integer,
    15: sa.types.Integer,
    16: sa.types.Boolean,
    17: sa.types.Float,
    18: sa.types.Float,
    19: sa.types.Float,
    20: sa.types.TIMESTAMP,
    21: sa.types.String,
    25: sa.types.String,
    26: sa.types.String,
    28: sa.types.Float,
    29: sa.types.Float,
    30: sa.types.DateTime,
    31: sa.types.Float,
}


class ActainCompiler(sa.sql.compiler.SQLCompiler):
    def get_select_precolumns(self, select):
        s = 'DISTINCT ' if select._distinct else ''
        if select._limit:
            s += 'TOP {0} '.format(select._limit)
        if select._offset:
            raise sa.exc.InvalidRequestError(
                "Pervasive PSQL does not support limit with an offset")
        return s

    def limit_clause(self, select):
        return ''

    def visit_true(self, expr, **kw):
        return '1'

    def visit_false(self, expr, **kw):
        return '0'


class ActainDialect(sa.engine.default.DefaultDialect):
    name = 'actain'
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
                typ = sa.types.LargeBinary
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
