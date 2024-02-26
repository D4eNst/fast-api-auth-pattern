import datetime


def format_datetime_into_isoformat(date_time: datetime.datetime) -> str:
    return date_time.replace(tzinfo=datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def format_dict_key_to_camel_case(dict_key: str) -> str:
    return "".join(
        word if idx == 0 else word.capitalize()
        for idx, word in enumerate(dict_key.split("_"))
    )
