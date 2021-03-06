import asyncio
from datasette import hookimpl
from datasette.utils.asgi import NotFound
import janus
from sqlite_dump import iterdump


END = object()


async def backup_sql(request, datasette, send):
    dbname = request.url_vars["database"]
    try:
        db = datasette.get_database(dbname)
    except KeyError:
        raise NotFound("Invalid database: {}".format(dbname))
    queue = janus.Queue()

    def dump(conn):
        for line in iterdump(conn):
            queue.sync_q.put(line)
        queue.sync_q.put(END)

    asyncio.ensure_future(db.execute_fn(dump))

    first = True
    while True:
        if first:
            await send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [[b"content-type", b"text/plain; charset=utf-8"]],
                }
            )
            first = False
        line = await queue.async_q.get()
        queue.async_q.task_done()
        if line is END:
            await send(
                {
                    "type": "http.response.body",
                    "body": b"\n",
                }
            )
            queue.close()
            await queue.wait_closed()
            return
        else:
            await send(
                {
                    "type": "http.response.body",
                    "body": (line + "\n").encode("utf-8"),
                    "more_body": True,
                }
            )


@hookimpl
def register_routes():
    return [
        (r"^/-/backup/(?P<database>[^/]+)\.sql$", backup_sql),
    ]
