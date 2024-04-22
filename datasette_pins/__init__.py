from datasette import hookimpl, Response
from .internal_migrations import internal_migrations
from sqlite_utils import Database
import json

@hookimpl
async def startup(datasette):
    def migrate(connection):
        db = Database(connection)
        internal_migrations.apply(db)

    await datasette.get_internal_database().execute_write_fn(migrate)

from urllib.parse import quote_plus


@hookimpl
def table_actions(datasette, actor, database, table):
    if actor:# and actor.get("id") == "root":
        #
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
          }}).then( () => window.reload())
        """
        return [
            {
                "href": f"javascript:{(js)}",
                "label": "Pin",
                "description": "Add, remove, rename or alter columns for this table.",
            }
        ]

@hookimpl
def top_homepage(datasette, request):
    async def f():
        rows = await datasette.get_internal_database().execute(
            """
              select *
              from datasette_pins_global_pinned_items
              order by order_idx
            """
            );
        data = json.dumps([dict(row) for row in rows])
        d = f"<div id='datasette-pins-homepage-target'></div> <script id='data' type=\"application/json\">{data}</script>"
        return d
    return f()

class Routes:

    async def global_pins(scope, receive, datasette, request):
        rows = await datasette.get_internal_database().execute(
            """
              select id, *
              from datasette_pins_global_pinned_items
              order by order_idx
            """
            );
        data = [dict(row) for row in rows]
        return Response.json({"ok": True, "data": data})

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

    async def reorder_view(scope, receive, datasette, request):
        return Response.html(
            await datasette.render_template(
                "reorder_view.html",
                request=request,
            )
        )

    async def reorder(scope, receive, datasette, request):
        if request.method != "POST":
            return Response.text("", status=405)

        actor_id = request.actor.get("id")

        data = json.loads((await request.post_body()).decode("utf8"))
        new_order = data["new_order"]
        assert type(new_order) is list
        for item in new_order:
            print(item)
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
def extra_css_urls(template, database, table, columns, view_name, request, datasette):
    async def inner():
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
        if view_name == 'index':
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
        (r"^/-/datasette-pins/api/reorder$", Routes.reorder),
        (r"^/-/datasette-pins/$", Routes.reorder_view),
    ]
