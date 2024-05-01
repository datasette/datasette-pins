from sqlite_utils import Database
from sqlite_migrate import Migrations
from pathlib import Path

internal_migrations = Migrations("datasette-pins.internal")


@internal_migrations()
def m001_initial(db: Database):
    db.executescript(
        """
          CREATE TABLE datasette_pins_global_pinned_items(
            id integer primary key autoincrement,

            --- Datasette actor ID of the user who pinned the item
            pinner_actor_id text,

            -- 'home' or 'database'
            pin_location text,

            -- 'database', 'table', 'canned_query', or plugin-defined string
            item_type text,

            ---
            origin_database text,
            ---
            origin_table text,

            identifier text,

            ---
            order_idx integer
          );
        """
    )
