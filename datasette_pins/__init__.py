from datasette import hookimpl, Response
from .internal_migrations import internal_migrations
from sqlite_utils import Database
import json
from functools import wraps
from datasette import hookimpl, Response, Permission, Forbidden

READ_PERMISSIONS = "datasette-pins-read"
WRITE_PERMISSIONS = "datasette-pins-write"


def check_permission(write=False):
    def decorator(func):
        @wraps(func)
        async def wrapper(scope, receive, datasette, request):
            if write:
                result = await datasette.permission_allowed(
                    request.actor, WRITE_PERMISSIONS, default=False
                )
            else:
                result = await datasette.permission_allowed(
                    request.actor, READ_PERMISSIONS, default=False
                )
            if not result:
                raise Forbidden("Permission denied for datasette-pins")
            return await func(scope, receive, datasette, request)

        return wrapper

    return decorator


@hookimpl
async def startup(datasette):
    def migrate(connection):
        db = Database(connection)
        internal_migrations.apply(db)

    await datasette.get_internal_database().execute_write_fn(migrate)


class Routes:
    @check_permission()
    async def global_pins(scope, receive, datasette, request):
        rows = await datasette.get_internal_database().execute(
            """
              select id, *
              from datasette_pins_global_pinned_items
              order by order_idx
            """
        )
        data = [dict(row) for row in rows]
        return Response.json({"ok": True, "data": data})

    @check_permission(write=True)
    async def pin(scope, receive, datasette, request):
        if request.method != "POST":
            return Response.text("", status=405)

        actor_id = request.actor.get("id")

        data = json.loads((await request.post_body()).decode("utf8"))
        item_type = data.get("item_type")
        origin_database = data.get("origin_database")
        origin_table = data.get("origin_table")
        await datasette.get_internal_database().execute_write(
            """
                insert into datasette_pins_global_pinned_items
                  (pinner_actor_id, pin_location, item_type, origin_database, origin_table, identifier, order_idx)
                VALUES
                  (:pinner_actor_id, 'home', :item_type, :origin_database, :origin_table, null, 1)
            """,
            {
                "pinner_actor_id": actor_id,
                "item_type": item_type,
                "origin_database": origin_database,
                "origin_table": origin_table,
            },
            block=True,
        )

        return Response.json({"ok": True})

    @check_permission(write=True)
    async def unpin(scope, receive, datasette, request):
        if request.method != "POST":
            return Response.text("", status=405)

        actor_id = request.actor.get("id")

        data = json.loads((await request.post_body()).decode("utf8"))
        item_id = data.get("item_id")
        await datasette.get_internal_database().execute_write(
            """
                DELETE FROM datasette_pins_global_pinned_items
                WHERE rowid = :item_id
            """,
            {
                "item_id": item_id,
            },
            block=True,
        )

        return Response.json({"ok": True})

    @check_permission(write=True)
    async def reorder_view(scope, receive, datasette, request):
        return Response.html(
            await datasette.render_template(
                "reorder_view.html",
                request=request,
            )
        )

    @check_permission(write=True)
    async def reorder(scope, receive, datasette, request):
        if request.method != "POST":
            return Response.text("", status=405)

        actor_id = request.actor.get("id")

        data = json.loads((await request.post_body()).decode("utf8"))
        new_order = data["new_order"]
        # TODO proper error handling
        assert type(new_order) is list
        for item in new_order:
            assert type(item) is dict
            assert type(item.get("id")) is int
            assert type(item.get("order_idx")) is int
        await datasette.get_internal_database().execute_write(
            """
                WITH new_order AS (
                  SELECT
                    json_extract(value, '$.id') AS id,
                    json_extract(value, '$.order_idx') AS order_idx
                  FROM json_each(:new_order)
                )
                UPDATE datasette_pins_global_pinned_items AS global_pinned_items
                SET order_idx = new_order.order_idx
                FROM new_order
                WHERE global_pinned_items.id = new_order.id
            """,
            {
                "new_order": json.dumps(new_order),
            },
            block=True,
        )

        return Response.json({"ok": True})


@hookimpl
async def table_actions(datasette, actor, database, table):
    if not (
        await datasette.permission_allowed(actor, READ_PERMISSIONS, default=False)
        or await datasette.permission_allowed(actor, WRITE_PERMISSIONS, default=False)
    ):
        return
    pin_id = await datasette.get_internal_database().execute(
        """
        select id
        from datasette_pins_global_pinned_items
        where item_type == "table"
          and origin_database = ?
          and origin_table = ?
        limit 1
        """,
        [database, table],
    )

    if len(pin_id) == 0:
        js = f"""
        fetch("/-/datasette-pins/api/pin", {{
          method: "POST",
          headers: {{
            "Content-Type": "application/json",
          }},
          body: JSON.stringify({{
            item_type: {json.dumps("table")},
            origin_database: {json.dumps(database)},
            origin_table: {json.dumps(table)},
          }})
        }}).then( () => window.location.reload())
      """
        return [
            {
                "href": f"javascript:{(js)}",
                "label": "Pin",
                "description": "Pin this table to the homepage",
            }
        ]
    js = f"""
      fetch("/-/datasette-pins/api/unpin", {{
        method: "POST",
        headers: {{
          "Content-Type": "application/json",
        }},
        body: JSON.stringify({{
          item_id: {json.dumps(pin_id.single_value())},
        }})
      }}).then( () => window.location.reload())
    """
    return [
        {
            "href": f"javascript:{(js)}",
            "label": "Unpin",
            "description": "Remove this table from the homepage pinned section",
        }
    ]


@hookimpl
async def database_actions(datasette, actor, database):
    if not (
        await datasette.permission_allowed(actor, READ_PERMISSIONS, default=False)
        or await datasette.permission_allowed(actor, WRITE_PERMISSIONS, default=False)
    ):
        return
    pin_id = await datasette.get_internal_database().execute(
        """
        select id
        from datasette_pins_global_pinned_items
        where item_type == "database"
          and origin_database = ?
        limit 1
        """,
        [database],
    )

    if len(pin_id) == 0:
        js = f"""
        fetch("/-/datasette-pins/api/pin", {{
          method: "POST",
          headers: {{
            "Content-Type": "application/json",
          }},
          body: JSON.stringify({{
            item_type: {json.dumps("database")},
            origin_database: {json.dumps(database)},
          }})
        }}).then( () => window.location.reload())
      """
        return [
            {
                "href": f"javascript:{(js)}",
                "label": "Pin",
                "description": "Pin this database to the homepage",
            }
        ]
    js = f"""
      fetch("/-/datasette-pins/api/unpin", {{
        method: "POST",
        headers: {{
          "Content-Type": "application/json",
        }},
        body: JSON.stringify({{
          item_id: {json.dumps(pin_id.single_value())},
        }})
      }}).then( () => window.location.reload())
    """
    return [
        {
            "href": f"javascript:{(js)}",
            "label": "Unpin",
            "description": "Remove this database from the homepage pinned section",
        }
    ]


@hookimpl
async def query_actions(datasette, actor, database, query_name):
    if await datasette.permission_allowed(
        actor, READ_PERMISSIONS, default=False
    ) or await datasette.permission_allowed(actor, WRITE_PERMISSIONS, default=False):
        pin_id = await datasette.get_internal_database().execute(
            """
            select id
            from datasette_pins_global_pinned_items
            where item_type == "canned_query"
              and origin_database = ?
              and origin_table = ?
            limit 1
            """,
            [database, query_name],
        )

        if len(pin_id) == 0:
            js = f"""
            fetch("/-/datasette-pins/api/pin", {{
              method: "POST",
              headers: {{
                "Content-Type": "application/json",
              }},
              body: JSON.stringify({{
                item_type: {json.dumps("canned_query")},
                origin_database: {json.dumps(database)},
                origin_table: {json.dumps(query_name)},
              }})
            }}).then( () => window.location.reload())
          """
            return [
                {
                    "href": f"javascript:{(js)}",
                    "label": "Pin",
                    "description": "Pin this table to the homepage",
                }
            ]
        js = f"""
          fetch("/-/datasette-pins/api/unpin", {{
            method: "POST",
            headers: {{
              "Content-Type": "application/json",
            }},
            body: JSON.stringify({{
              item_id: {json.dumps(pin_id.single_value())},
            }})
          }}).then( () => window.location.reload())
        """
        return [
            {
                "href": f"javascript:{(js)}",
                "label": "Unpin",
                "description": "Remove this table from the homepage pinned section",
            }
        ]


@hookimpl
def top_homepage(datasette, request):
    async def f():
        if not (
            await datasette.permission_allowed(
                request.actor, READ_PERMISSIONS, default=False
            )
            or await datasette.permission_allowed(
                request.actor, WRITE_PERMISSIONS, default=False
            )
        ):
            return ""
        rows = await datasette.get_internal_database().execute(
            """
              select *
              from datasette_pins_global_pinned_items
              order by order_idx
            """
        )
        data = [dict(row) for row in rows]
        for i, row in enumerate(rows):
            metadata = datasette.metadata(
                database=row["origin_database"],
                table=row["origin_table"],
                fallback=False,
            )
            data[i]["metadata"] = metadata

        d = f"<div id='datasette-pins-homepage-target'></div> <script id='datasette-pins-homepage-data' type=\"application/json\">{json.dumps(data)}</script>"
        return d

    return f()


@hookimpl
def extra_css_urls(template, database, table, columns, view_name, request, datasette):
    async def inner():
        if view_name == "index" and (
            await datasette.permission_allowed(
                request.actor, READ_PERMISSIONS, default=False
            )
            or await datasette.permission_allowed(
                request.actor, WRITE_PERMISSIONS, default=False
            )
        ):
            return [
                datasette.urls.path(
                    "/-/static-plugins/datasette-pins/home/index.min.css"
                )
            ]
        return []

    return inner


@hookimpl
def extra_js_urls(template, database, table, columns, view_name, request, datasette):
    async def inner():
        if view_name == "index" and (
            await datasette.permission_allowed(
                request.actor, READ_PERMISSIONS, default=False
            )
            or await datasette.permission_allowed(
                request.actor, WRITE_PERMISSIONS, default=False
            )
        ):
            return [
                datasette.urls.path(
                    "/-/static-plugins/datasette-pins/home/index.min.js"
                )
            ]
        return []

    return inner


@hookimpl
def register_routes():
    return [
        (r"^/-/datasette-pins/api/global_pins$", Routes.global_pins),
        (r"^/-/datasette-pins/api/pin$", Routes.pin),
        (r"^/-/datasette-pins/api/unpin$", Routes.unpin),
        (r"^/-/datasette-pins/api/reorder$", Routes.reorder),
        (r"^/-/datasette-pins/$", Routes.reorder_view),
    ]


@hookimpl
def register_permissions(datasette):
    return [
        Permission(
            name=WRITE_PERMISSIONS,
            abbr=None,
            description="Can pin, unpin, and re-order pins for datasette-pins",
            takes_database=False,
            takes_resource=False,
            default=False,
        ),
        Permission(
            name=READ_PERMISSIONS,
            abbr=None,
            description="Can read pinned items.",
            takes_database=False,
            takes_resource=False,
            default=False,
        ),
    ]
