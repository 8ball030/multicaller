
from datetime import datetime, timedelta
from packages.valory.customs.trend_following_strategy.trend_following_strategy import run, transform

data = """{"Date Time":{"0":"2021-01-01 00:00:00","1":"2021-01-01 00:05:00","2":"2021-01-01 00:10:00","3":"2021-01-01 00:15:00","4":"2021-01-01 00:20:00","5":"2021-01-01 00:25:00","6":"2021-01-01 00:30:00","7":"2021-01-01 00:35:00","8":"2021-01-01 00:40:00","9":"2021-01-01 00:45:00"},"Open":{"0":0.0,"1":0.1,"2":0.2,"3":0.3,"4":0.4,"5":0.5,"6":0.6,"7":0.7,"8":0.8,"9":0.9},"High":{"0":0.0,"1":0.1,"2":0.2,"3":0.3,"4":0.4,"5":0.5,"6":0.6,"7":0.7,"8":0.8,"9":0.9},"Low":{"0":0.0,"1":0.1,"2":0.2,"3":0.3,"4":0.4,"5":0.5,"6":0.6,"7":0.7,"8":0.8,"9":0.9},"Close":{"0":0.0,"1":0.1,"2":0.2,"3":0.3,"4":0.4,"5":0.5,"6":0.6,"7":0.7,"8":0.8,"9":0.9},"Volume":{"0":0,"1":10,"2":20,"3":30,"4":40,"5":50,"6":60,"7":70,"8":80,"9":90}}"""

token = 'OLAS'



def date_range(start_date, end_date, seconds_delta=300):
    """
    Generate a range of dates in the format 'YYYY-MM-DD HH:MM:SS'.
    """
    start = datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S')
    end = datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S')
    current = start
    while current < end:
        yield current.timestamp() * 1000
        current += timedelta(seconds=seconds_delta)

raw_price_data = [
    [date, i * 0.1] for i, date in enumerate(date_range('2021-01-01T00:00:00', '2021-01-01T00:50:00'))
]

raw_volume_data = [
    [date, i * 10] for i, date in enumerate(date_range('2021-01-01T00:00:00', '2021-01-01T00:50:00'))
]

def test_run():
    """
    Test the run function.
    """

    res = run(**{'transformed_data': data,})

def test_transform():
    """
    Test the transform function.
    """
    output = transform(raw_price_data, raw_volume_data)
    assert output is not None
    assert output == data


