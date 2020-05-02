import sqlalchemy as sa
import turbodbc
import decimal


class _TurboDecimal(sa.types.DECIMAL):
    """Handle Decimal types since Turbodbc doesn't support it natively.
    Adapted from https://github.com/blue-yonder/sqlalchemy_exasol
    source file: sqlalchemy_exasol/turbodbc.py
    Copyright (c) 2016-2017 Blue Yonder GmbH
    """

    def bind_processor(self, dialect):
        return super(_TurboDecimal, self).bind_processor(dialect)

    def result_processor(self, dialect, coltype):
        if self.asdecimal:
            fstring = "%%.%df" % self._effective_decimal_return_scale

            def to_decimal(value):
                if value is None:
                    return None
                elif isinstance(value, decimal.Decimal):
                    return value
                elif isinstance(value, float):
                    return decimal.Decimal(fstring % value)
                else:
                    return decimal.Decimal(value)

            return to_decimal
        else:
            return None


class TurbODBCConnector(sa.connectors.Connector):
    driver = 'turbodbc'

    supports_sane_multi_rowcount = False

    supports_unicode_statements = True
    supports_unicode_binds = True

    supports_native_decimal = False
    colspecs = {sa.types.Numeric: _TurboDecimal}

    @classmethod
    def dbapi(cls):
        return __import__('turbodbc')

    def create_connect_args(self, url):
        """Create the connect args for Turbodbc.
        Some code adapted from the Pyodbc connector in the SQLAlchemy
        codebase.
        """

        options = url.translate_connect_args(username='user')
        query = url.query
        options.update(query)

        connect_args = {}

        # first get the Turbodbc specific options
        turbodbc_options = {'read_buffer_size': turbodbc.Rows(50000)}
        for param in ('read_buffer_size', 'parameter_sets_to_buffer',
                      'use_async_io'):
            if param in options:
                raw = options.pop(param)
                if param == 'use_async_io':
                    value = sa.util.asbool(raw)
                if param == 'read_buffer_size':
                    value = turbodbc.Rows(sa.util.asint(raw))
                else:
                    value = sa.util.asint(raw)
                turbodbc_options[param] = value

        connect_args['turbodbc_options'] = turbodbc.make_options(
            prefer_unicode=True,
            **turbodbc_options)
        for param in ('ansi', 'unicode_results', 'autocommit'):
            if param in options:
                connect_args[param] = sa.util.asbool(options.pop(param))

        dsn_connection = 'dsn' in options or \
            ('host' in options and 'database' not in options)
        if dsn_connection:
            dsn = [options.pop('host', '') or options.pop('dsn', '')]
        else:
            dsn = []
            port = ''
            if 'port' in options and 'port' not in query:
                port = int(options.pop('port'))

            driver = options.pop('driver', None)
            if driver is None:
                sa.util.warn(
                    "No driver name specified; "
                    "this is expected by ODBC when using "
                    "DSN-less connections")
            else:
                connect_args['driver'] = driver

            connect_args.update(
                server=(options.pop('host', '')),
                port=port,
                database=options.pop('database', '')
            )

        user = options.pop('user', None)
        if user:
            connect_args.update(
                uid=user,
                pwd=options.pop('password', '')
            )
        else:
            connect_args['trusted_connection'] = 'Yes'

        return [dsn, connect_args]

    def is_disconnect(self, e, connection, cursor):
        if isinstance(e, self.dbapi.Error):
            return '[08S01]' in str(e)
        else:
            return False
