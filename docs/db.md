## Database layout

The database layout is defined in `bpo/db/__init__.py`. The initial layout of
each table **must not be modified**, unless following strict rules listed
below. Otherwise the live deployment of the bpo server can't migrate properly
to the new version. Remember that we roll out each commit that is pushed to
master automatically to the live instance.

### Extending the DB layout
Using a "proper" migration framework was considered, but the amount of effort
to write migrations would be overkill for this small project. Instead, the
tables always get bootstrapped from version 0 to latest.

#### New column

1. Extend `bpo/db/migrate.py:upgrade()` with a new entry like the following:

```py
def upgrade():
    ...
    # Log: add column "commit"
    if version_get() == 1:
        engine.execute("ALTER TABLE 'log' ADD COLUMN 'commit' VARCHAR")
        version_set(2)
```

2. Extend the table's class in `bpo_db/__init_.py`. Use `system=True` so
   sqlalchemy will not attempt to create the column. Add a comment indicating
   the migration version that will create the table.

```py
class Log(base):
    __tablename__ = "log"

    # === DATABASE LAYOUT, DO NOT CHANGE! (read docs/db.md) ===
    ...
    commit = Column(String, system=True)  # [v2]
    # === END OF DATABASE LAYOUT ===
```

#### New index

1. Extend `bpo/db/migrate.py:upgrade()` with a new entry like the following:

```py
def upgrade():
    ...
    # Package: add index "status"
    if version_get() == 2:
        engine.execute("CREATE INDEX 'status'"
                       "ON 'package' (`status`)")
        version_set(3)
```

2. Extend the table's class in `bpo_db/__init_.py` with an commented out entry
   of the new index, and the migration version that creates it.

```py
class Log(base):
    __tablename__ = "log"

    # === DATABASE LAYOUT, DO NOT CHANGE! (read docs/db.md) ===
    ...
    # [v3]: Index("status", Package.status)
    # === END OF DATABASE LAYOUT ===
```
