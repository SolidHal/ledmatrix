#!/usr/bin/env python3
import asyncio
import logging
import time

import caldav

#TODO importing config before other modules breaks imports for some reason
from . import config

class Todo:
    def __init__(self, due_date, summary):
        self._due_date = due_date
        self._summary = summary

    def summary(self):
        return self._summary

    # returns a datetime.datetime
    def due(self):
        return self._due_date

    def __repr__(self):
        return f"{self._due_date} :: {self._summary}"

async def get_calendars(caldav_url, username, password):

    # async wrappers for caldav lib
    async def get_principal(client):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None,  client.principal,)

    async def get_calendars_list(principal):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None,  principal.calendars,)

    client = caldav.DAVClient(url=caldav_url, username=username, password=password)
    my_principal = await get_principal(client)

    ## The principals calendars can be fetched like this:
    return await get_calendars_list(my_principal)


async def get_todos(caldav_url, username, password):

    async def get_todos_list(calendar):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None,  lambda: calendar.todos(sort_keys=None), )

    calendars = await get_calendars(caldav_url, username, password)

    due_todos = []
    for c in calendars:
        #TODO add config var for the todo list caldav name to get
        # seems we will have to fuzzy match this
        if "Reminders" in c.name:
            # print(c.get_supported_components()) # only component is VTODOS
            try:
                # todos = c.todos(sort_keys=None)
                todos = await get_todos_list(c)
            except Exception as e:
                print("""
                must set filter one in caldav.objects.Calendar.todos to
                filters1 = cdav.CompFilter("VTODO")
                to avoid errors
                """)
                raise

            for obj in todos:
                # skip all todos that are not "due"
                if hasattr(obj.vobject_instance.vtodo, "due"):
                    t = Todo(obj.vobject_instance.vtodo.due.value, obj.vobject_instance.vtodo.summary.value)
                    due_todos.append(t)
    return due_todos
