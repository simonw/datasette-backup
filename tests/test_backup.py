from datasette.app import Datasette
import pytest
import sqlite_utils
import sqlite3
import textwrap
import re


@pytest.fixture(scope="session")
def ds(tmp_path_factory):
    db_directory = tmp_path_factory.mktemp("dbs")
    db_path = db_directory / "test.db"
    db = sqlite_utils.Database(db_path)
    db["dogs"].insert_all(
        [{"id": 1, "name": "Cleo", "age": 5}, {"id": 2, "name": "Pancakes", "age": 4}],
        pk="id",
    )
    return Datasette([str(db_path)])


@pytest.mark.asyncio
async def test_plugin_is_installed():
    ds = Datasette([], memory=True)
    response = await ds.client.get("/-/plugins.json")
    assert 200 == response.status_code
    installed_plugins = {p["name"] for p in response.json()}
    assert "datasette-backup" in installed_plugins


@pytest.mark.asyncio
async def test_backup_sql(ds):
    assert (await ds.client.get("/-/backup/nope.sql")).status_code == 404
    response = await ds.client.get("/-/backup/test.sql")
    assert response.status_code == 200
    normalized_sql = re.sub(r'["\[]([^"\]]+)["\]]', r"[\1]", response.text)
    expected_sql = textwrap.dedent("""
        BEGIN TRANSACTION;
        CREATE TABLE IF NOT EXISTS [dogs] (
            [id] INTEGER PRIMARY KEY,
            [name] TEXT,
            [age] INTEGER
        );
        INSERT INTO [dogs] VALUES(1,'Cleo',5);
        INSERT INTO [dogs] VALUES(2,'Pancakes',4);
        COMMIT;
    """)
    assert [line.strip() for line in normalized_sql.strip().splitlines()] == [
        line.strip() for line in expected_sql.strip().splitlines()
    ]


@pytest.mark.asyncio
async def test_backup_sql_fts(tmpdir):
    db_path = str(tmpdir / "fts.db")
    db = sqlite_utils.Database(db_path)
    db["dogs"].insert_all(
        [{"id": 1, "name": "Cleo", "age": 5}, {"id": 2, "name": "Pancakes", "age": 4}],
        pk="id",
    )
    db["dogs"].enable_fts(["name"])
    ds = Datasette([db_path])
    response = await ds.client.get("/-/backup/fts.sql")
    assert response.status_code == 200
    restore_db_path = str(tmpdir / "restore.db")
    sqlite3.connect(restore_db_path).executescript(response.text)
    restore_db = sqlite_utils.Database(restore_db_path)
    assert restore_db["dogs"].detect_fts() == "dogs_fts"
    normalized_schema = re.sub(
        r'["\[]([^"\]]+)["\]]', r"[\1]", restore_db["dogs_fts"].schema
    )
    assert normalized_schema.startswith("CREATE VIRTUAL TABLE [dogs_fts] USING FTS")
