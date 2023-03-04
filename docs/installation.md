# Installing package

```shell
pip install sqlaurum
```
or

```shell
poetry install sqlaurum
```

### Installing optional dependencies:

```shell
pip install 'sqlaurum[extension]'
```

### Available extensions:

- `asyncpg`
- `aiosqlite`
- `alembic`

### Installing multiple extensions:

```shell
pip install 'sqlaurum[asyncpg, alembic]'
```

### Installing all

```shell
pip install 'sqlaurum[all]'
```