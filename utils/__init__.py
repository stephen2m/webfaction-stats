import structlog
import datetime
import json


def _add_timestamp(_, __, event_dict):
    event_dict['timestamp'] = datetime.datetime.utcnow()
    return event_dict


def _serializer(obj):
    """
    Render particular types in an appropriate way for logging. Allow
    the json module to handle the rest as usual.
    """
    # Datetime-like objects
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    else:
        return "Object type {obj} with value {value} is not JSON \
                serializable".format(obj=type(obj), value=repr(obj))


class KeyValueRenderer(object):
    """
    Render event_dict as a list of Key=json.dumps(str(Value)) pairs.

    This is a drop-in replacement for the structlog
    KeyValueRenderer. The primary motivation for using it is to avoid
    logging Python object representations for things like datetimes
    and unicode strings. json.dumps ensures that strings are
    double-quoted, with embedded quotes conveniently escaped.
    """

    def __call__(self, logger, name, event_dict):
        def serialize(value):
            """
            serialize dict objects without appending extra escape xters
            """
            try:
                value = json.loads(value)
            except Exception:
                pass

            return json.dumps(value, default=_serializer)

        return ', '.join('{key}={value}'.format(
            key=key, value=serialize(value)
        ) for key, value in event_dict.items())

structlog.configure(
    processors=[
        structlog.processors.UnicodeEncoder(),
        KeyValueRenderer(),
        _add_timestamp
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)