import datetime
import http.client
import json
from typing import List

import dateutil.parser
import flask
import pytz


def get_next_connections(line: str, stop: str, terminus: str) -> List[str]:
    connection = http.client.HTTPConnection('timetable.search.ch')
    connection.request('GET', f'/api/stationboard.json?stop={stop}&limit=20')
    result = json.loads(connection.getresponse().read())
    zurich_tz = pytz.timezone('Europe/Zurich')
    zurich_time = datetime.datetime.now().astimezone(zurich_tz)
    connections = []

    for connection in result['connections']:
        if connection['line'] == line and connection['terminal']['id'] == terminus:
            connection_time = zurich_tz.localize(dateutil.parser.parse(connection['time']))
            delta = connection_time - zurich_time
            if delta < datetime.timedelta(minutes=1) or delta > datetime.timedelta(hours=1):
                continue

            connections.append(f'{delta.seconds / 60:d} min ({connection_time.strftime("%H:%M")})')
            if len(connections) >= 5:
                break

    return connections


def next_times(request: flask.Request):
    """
    Args:
        request (flask.Request): The request object.
        <http://flask.pocoo.org/docs/1.0/api/#flask.Request>"""

    connections = get_next_connections(request.args['line'], request.args['stop'],
                                       request.args['terminus'])

    result = {'frames': []}
    if len(connections) == 0:
        result['frames'].append({
            'text': 'No buses in the next hour',
            'icon': 'i996',
        })
    else:
        result['frames'].append({
            'text': 'Next 31 buses:',
            'icon': 'i996',
        })
        result['frames'].append({
            'text': ', '.join(connections),
            'icon': 'a82',
        })
    return json.dumps(result)
