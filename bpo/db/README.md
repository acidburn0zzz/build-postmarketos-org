### bpo.db

* each table has its own file
* each of these table files has python functions to access the SQL database
* mapping of function names to SQL statements:
  * `${table}_insert()` -> `INSERT`
  * `${table}_get_by_${column}()` -> `SELECT`
  * `${table}_set_by_${column}()` -> `UPDATE`
  * `${table}_delete_by_${column}()` -> `DELETE`
* variable names are the same as column names
* only implement functions, that are used
* each function has a "commit=True" argument, and at the end:
```
if commit:
    args.db.commit()
```
