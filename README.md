# freqsignals-client

[FreqSignals](https://freqsignals.com) client for python! It assists in token management and abstracts the HTTP requests to make it easy to upload or download signals.

## Install

```bash
pip install freqsignals-client
```

## Docs

### FreqSignalsClient

#### init
```python
from freqsignals_client import FreqSignalsClient,
client = FreqSignalsClient(
    client_id="1234",
    client_secret="567890",
)
```

#### get_signals
[see documentation](https://freqsignals.com/documentation#oauth2-api-token-integration)

```python
# get all signals
client.get_signals()
# pass some filters as a dict of query parameters (see documentation)
client.get_signals({
    "data_set_id": "1234-56-78-9012",
    "updated_date__gt": "2023-01-01",
    "limit": 1,
})
```

_Note_: Might raise a `freqsignals_client.FreqSignalsError` if FreqSignals rejects the request

_Note_: Might raise a `freqsignals_client.FreqSignalsTimeoutError` if the request times out

which returns:
```
{
    "count": 420,
    "next": "https://api.freqsignals.com/api/crud/signals/?limit=1&offset=1",
    "previous": null,
    "results": [
      {
        "id": "1237-45-67-8910",
        "symbol": "DOGE/USDT",
        "value": 48.965,
        "ttl_minutes": 5,
        "created_date": "2022-11-13T22:52:58.216164Z",
        "updated_date": "2023-01-26T23:25:46.360932Z",
        "context": {
          "rsi": 48.965,
          "price": 0.086,
          "open": 0.086,
          "close": 0.086,
          "high": 0.086,
          "low": 0.086,
          "last_move": 0.0
        },
        "data_set_id": "2345-67-89-1234"
      }
    ]
}
```

#### post_signal
[see documentation](https://freqsignals.com/documentation#oauth2-api-token-integration)

```python
client.post_signal({
    "symbol": "BTC",
    "value": 0.1,
    "ttl_minutes": 60,
    "data_set_id": "DATA_SET_ID"
})
```

#### logging
To get visibility into logged events, override the log method and log however your app needs to log:
```python
class CustomFreqSignalsClass(FreqSignalsClient):
    def log(self, level, msg, **log_variables):
        print(f"[{level}] {msg}", log_variables)
        

client = CustomFreqSignalsClass(client_id, client_secret)
```

## Example
```python
from freqsignals import FreqSignalsClient, FreqSignalsError, FreqSignalsTimeoutError

my_client = FreqSignalsClient("1234", "56-789")
try:
    results = my_client.get_signals()
    print(results)
except FreqSignalsError:
    print("FreqSignals failure")
except FreqSignalsTimeoutError:
    print("FreqSignals timed out")
```

## Common Commands:

Black Formatting
```bash
$ black freqsignals_client --config freqsignals_client.toml
```

Build
```bash
$ python3 setup.py sdist
```

Pypi Distribution
```bash
$ python3 -m twine upload dist/*
```

## License

FreqSignals Client is [MIT licensed](./LICENSE).
