import time
import os
import json
import requests
from urllib.parse import urlencode
from datetime import datetime, timedelta

from requests.exceptions import ConnectTimeout, RequestException
from .exceptions import FreqSignalsError, FreqSignalsTimeoutError


DEFAULT_HOST = os.environ.get("FREQSIGNALS_HOST", "api.freqsignals.com")
DEFAULT_HTTPS = str(os.environ.get("FREQSIGNALS_HTTPS", "1")) != "0"
DEFAULT_CLIENT_ID = os.environ.get("FREQSIGNALS_CLIENT_ID")
DEFAULT_CLIENT_SECRET = os.environ.get("FREQSIGNALS_CLIENT_SECRET")
DEFAULT_REQUEST_TIMEOUT = 20
DEFAULT_REQUEST_MAX_ATTEMPTS = 2
DEFAULT_REQUEST_WAIT_INTERVAL = 1


class FreqSignalsClient:
    def __init__(
        self,
        client_id=DEFAULT_CLIENT_ID,
        client_secret=DEFAULT_CLIENT_SECRET,
        host=DEFAULT_HOST,
        https=DEFAULT_HTTPS,
        request_timeout=DEFAULT_REQUEST_TIMEOUT,
        request_max_attempts=DEFAULT_REQUEST_MAX_ATTEMPTS,
        request_wait_interval=DEFAULT_REQUEST_WAIT_INTERVAL,
        encoder_cls=None
    ):
        self._client_id = client_id
        self._client_secret = client_secret
        self._host = host
        self._https = https
        self._request_timeout = request_timeout
        self._request_max_attempts = request_max_attempts
        self._request_wait_interval = request_wait_interval
        self._has_attempted_token_refresh = False
        self._refresh_at = None
        self._token = None
        self._encoder_cls = encoder_cls

    def get_token(self):
        if self._token is None:
            post_data = {
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            }
            protocol_string = "https" if self._https else "http"
            url = f"{protocol_string}://{self._host}/oa2/token/"

            response = requests.post(url, json=post_data, verify=self._https)

            assert response.status_code == 200, response.json()
            res_data = response.json()
            assert "access_token" in res_data, res_data
            assert "expires_in" in res_data, res_data
            assert "scope" in res_data, res_data
            assert "token_type" in res_data, res_data
            self._refresh_at = datetime.now() + timedelta(seconds=res_data["expires_in"] - 60)
            self._token = res_data["access_token"]
        return self._token

    def get_headers(self):
        return {"Authorization": f"Bearer {self.get_token()}"}

    def get_full_url(self, url):
        protocol_string = "https" if self._https else "http"
        return f"{protocol_string}://{self._host}{url}"

    def make_request(self, url, method="get", data=None, headers=None, remaining_attempts=1):
        """
        Issues the request to FreqSignals
        Args:
            url: str - path to request
            method: str - get | post
            data: dict - optional - body of the post
            headers: dict - optional - headers to include
            remaining_attempts: how many more requests to make

        Returns:
            list - results or raises FreqSignalsError
        """
        data_response = None
        if self._refresh_at and datetime.now() > self._refresh_at:
            self._token = None
            self._refresh_at = None
        if headers == None:
            headers = self.get_headers()
        while data_response is None and remaining_attempts > 0:
            try:

                remaining_attempts -= 1
                if method == "get":
                    response = requests.get(
                        self.get_full_url(url), timeout=self._request_timeout, headers=headers, verify=self._https
                    )
                elif method == "post":
                    response = requests.post(
                        self.get_full_url(url),
                        timeout=self._request_timeout,
                        json=json.loads(json.dumps(data, cls=self._encoder_cls) if self._encoder_cls else json.dumps(data)),
                        headers={
                            'Content-Type': 'application/json',
                            **headers
                        },
                        verify=self._https,
                    )
                else:
                    raise FreqSignalsError(f"bad method: {method}")


                if response.status_code < 200 or response.status_code >= 300:
                    self.log(
                        "error",
                        "make_load_request.error_status_code",
                        remaining_attempts=remaining_attempts,
                        data=data,
                        status_code=response.status_code,
                        response=response.text,
                    )
                    if response.text:
                        raise FreqSignalsError(
                            "bad return status code: {} - {}".format(response.status_code, response.text)
                        )
                    else:
                        raise FreqSignalsError("bad return status code: {}".format(response.status_code))

                json_res = response.json()
                self.log(
                    "info",
                    "request.success",
                    remaining_attempts=remaining_attempts,
                    method=method,
                    url=url,
                    data=data,
                    status_code=response.status_code,
                    response=json_res,
                )
                return json_res

            except ConnectTimeout:
                self.log(
                    "error",
                    "request.timeout",
                    remaining_attempts=remaining_attempts,
                    method=method,
                    url=url,
                    data=data,
                )
                if remaining_attempts:
                    time.sleep(self._request_wait_interval)
                if not remaining_attempts:
                    raise FreqSignalsTimeoutError

            except RequestException:
                raise
        raise FreqSignalsTimeoutError()

    def get(self, url):
        return self.make_request(url=url, method="get")

    def post(self, url, data):
        return self.make_request(url=url, method="post", data=data)

    def post_signal(self, data):
        return self.post("/api/async/signals/", data)

    def get_signals(self, filters=None):
        if filters is None:
            filters = {}
        query_params = urlencode({**filters})
        return self.get(f"/api/crud/signals/?{query_params}")

    def get_signal_history(self, symbol, data_set_id, filters=None, multiple_pages=False):
        if filters is None:
            filters = {}
        query_params = urlencode({**filters})
        if multiple_pages:
            filters["limit"] = 1000
            filters["offset"] = 0
            historical_signals = []
            more_pages = True
            while more_pages:
                historical_signals_res = self.get(f"/api/crud/signal_history/?symbol={symbol}&data_set_id={data_set_id}&{query_params}")
                if historical_signals_res["results"]:
                    historical_signals += historical_signals_res["results"]
                    filters["offset"] = filters["offset"] + filters["limit"]
                    if (len(historical_signals_res["results"]) < filters["limit"]):
                        more_pages = False
                else:
                    more_pages = False
            return {
                "count": len(historical_signals),
                "results": historical_signals
            }

        else:
            return self.get(f"/api/crud/signal_history/?symbol={symbol}&data_set_id={data_set_id}&{query_params}")


    def log(self, level, msg, **kwargs):
        """
        Logging function hook that should be overridden if you want logging
        Args:
            level: str - the level to log at
            msg: str - the message
            kwargs: dict - any logging vars

        Returns:
            None
        """
        # print(json.dumps({"level": level, "msg": msg, "log_kwargs": kwargs}, cls=NpEncoder))
        pass
