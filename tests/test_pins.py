from datasette.app import Datasette
import pytest
import pytest_asyncio
import sqlite_utils


def cookie_for_actor(datasette, actor_id):
    return {"ds_actor": datasette.sign({"a": {"id": actor_id}}, "actor")}


@pytest_asyncio.fixture
async def ds_with_data(tmp_path_factory):
    """Create a Datasette instance with test data."""
    db_directory = tmp_path_factory.mktemp("dbs")
    db_path = db_directory / "test.db"
    db = sqlite_utils.Database(db_path)

    # Create a test table
    db["items"].insert_all(
        [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"},
        ]
    )

    # Create a SQL view
    db.execute("CREATE VIEW items_view AS SELECT * FROM items WHERE id > 0")

    # Create a Datasette instance with a canned query
    datasette = Datasette(
        [db_path],
        config={
            "databases": {
                "test": {"queries": {"test_query": {"sql": "select * from items"}}}
            }
        },
    )
    datasette.root_enabled = True
    await datasette.invoke_startup()
    return datasette


@pytest.mark.asyncio
async def test_plugin_is_installed():
    datasette = Datasette(memory=True)
    response = await datasette.client.get("/-/plugins.json")
    assert response.status_code == 200
    installed_plugins = {p["name"] for p in response.json()}
    assert "datasette-pins" in installed_plugins


@pytest.mark.asyncio
async def test_permissions():
    datasette = Datasette(
        memory=True,
        config={"permissions": {"datasette-pins-read": {"id": ["alex"]}}},
    )

    response = await datasette.client.get(
        "/-/datasette-pins/api/global_pins",
        cookies=cookie_for_actor(datasette, "alex"),
    )
    assert response.status_code == 200

    response = await datasette.client.get(
        "/-/datasette-pins/api/global_pins",
        cookies=cookie_for_actor(datasette, "unknown"),
    )
    assert response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "item_type,path",
    [
        ("table", "/test/items"),
        ("view", "/test/items_view"),
        ("database", "/test"),
        ("query", "/test/test_query"),
    ],
)
async def test_action_buttons_visibility_by_actor(ds_with_data, item_type, path):
    """Test that Pin action buttons are visible to root user but not to signed-out users."""
    datasette = ds_with_data

    # Root user should see Pin button
    root_cookies = {"ds_actor": datasette.client.actor_cookie({"id": "root"})}
    root_response = await datasette.client.get(path, cookies=root_cookies)
    assert root_response.status_code == 200
    assert "Pin" in root_response.text

    # Anonymous users should not see Pin/Unpin buttons
    anon_response = await datasette.client.get(path)
    assert anon_response.status_code == 200
    assert "/-/datasette-pins/api/pin" not in anon_response.text
    assert "/-/datasette-pins/api/unpin" not in anon_response.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "item_type,path,post_data",
    [
        (
            "table",
            "/test/items",
            {"item_type": "table", "origin_database": "test", "origin_table": "items"},
        ),
        (
            "view",
            "/test/items_view",
            {
                "item_type": "view",
                "origin_database": "test",
                "origin_table": "items_view",
            },
        ),
        ("database", "/test", {"item_type": "database", "origin_database": "test"}),
        (
            "query",
            "/test/test_query",
            {
                "item_type": "canned_query",
                "origin_database": "test",
                "origin_table": "test_query",
            },
        ),
    ],
)
async def test_unpin_button_appears_after_pinning(
    ds_with_data, item_type, path, post_data
):
    """Test that Unpin button appears after pinning an item."""
    datasette = ds_with_data
    root_cookies = {"ds_actor": datasette.client.actor_cookie({"id": "root"})}

    # Before pinning, should see "Pin"
    response = await datasette.client.get(path, cookies=root_cookies)
    assert response.status_code == 200
    # Check that we see the pin API endpoint but not yet unpin
    assert "/-/datasette-pins/api/pin" in response.text

    # Pin the item
    pin_response = await datasette.client.post(
        "/-/datasette-pins/api/pin",
        json=post_data,
        cookies=root_cookies,
    )
    assert pin_response.status_code == 200

    # After pinning, should see "Unpin" instead
    response_after = await datasette.client.get(path, cookies=root_cookies)
    assert response_after.status_code == 200
    assert "Unpin" in response_after.text
    assert "/-/datasette-pins/api/unpin" in response_after.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "item_type,origin_database,origin_table",
    [
        ("table", "test", "items"),
        ("view", "test", "items_view"),
        ("database", "test", None),
        ("canned_query", "test", "test_query"),
    ],
)
async def test_pin_functionality_by_actor(
    ds_with_data, item_type, origin_database, origin_table
):
    """Test that pinning works for root user but not for signed-out users."""
    datasette = ds_with_data

    # Prepare post data
    post_data = {
        "item_type": item_type,
        "origin_database": origin_database,
    }
    if origin_table:
        post_data["origin_table"] = origin_table

    # Root user can pin successfully
    root_response = await datasette.client.post(
        "/-/datasette-pins/api/pin",
        json=post_data,
        cookies=cookie_for_actor(datasette, "root"),
    )
    assert root_response.status_code == 200
    assert root_response.json()["ok"] is True

    # Verify the item was pinned
    pins_response = await datasette.client.get(
        "/-/datasette-pins/api/global_pins",
        cookies=cookie_for_actor(datasette, "root"),
    )
    assert pins_response.status_code == 200
    pins = pins_response.json()["data"]
    assert len(pins) == 1
    assert pins[0]["item_type"] == item_type
    assert pins[0]["origin_database"] == origin_database

    # Anonymous user cannot pin (gets 403)
    anon_response = await datasette.client.post(
        "/-/datasette-pins/api/pin",
        json=post_data,
    )
    assert anon_response.status_code == 403


@pytest.mark.asyncio
async def test_unpin_functionality_by_actor(ds_with_data):
    """Test that unpinning works for root user but not for signed-out users."""
    datasette = ds_with_data

    # First, pin an item as root
    await datasette.client.post(
        "/-/datasette-pins/api/pin",
        json={
            "item_type": "table",
            "origin_database": "test",
            "origin_table": "items",
        },
        cookies=cookie_for_actor(datasette, "root"),
    )

    # Get the pin ID
    pins_response = await datasette.client.get(
        "/-/datasette-pins/api/global_pins",
        cookies=cookie_for_actor(datasette, "root"),
    )
    pins = pins_response.json()["data"]
    pin_id = pins[0]["id"]

    # Anonymous user cannot unpin (gets 403)
    anon_response = await datasette.client.post(
        "/-/datasette-pins/api/unpin",
        json={"item_id": pin_id},
    )
    assert anon_response.status_code == 403

    # Root user can unpin successfully
    root_response = await datasette.client.post(
        "/-/datasette-pins/api/unpin",
        json={"item_id": pin_id},
        cookies=cookie_for_actor(datasette, "root"),
    )
    assert root_response.status_code == 200
    assert root_response.json()["ok"] is True

    # Verify the item was unpinned
    pins_response = await datasette.client.get(
        "/-/datasette-pins/api/global_pins",
        cookies=cookie_for_actor(datasette, "root"),
    )
    pins = pins_response.json()["data"]
    assert len(pins) == 0
