from .settings import DEFAULT_USER_AGENT
import requests
from requests.exceptions import ConnectionError
import time
import logging
logger = logging.getLogger(__name__)

class Session(object):
    def __init__(self,
        follow_redirects=False,
        user_agent=DEFAULT_USER_AGENT,
        max_retries=0,
    ):
        self.follow_redirects = follow_redirects
        self.user_agent = user_agent
        self.max_retries = max_retries

    def get(self, url, **kwargs):
        headers = {
            "User-Agent": self.user_agent,
        }
        response_is_final = False
        retries = 0
        while (response_is_final == False):
            try:
                res = requests.get(
                    url,
                    allow_redirects=self.follow_redirects,
                    headers=headers,
                    stream=True,
                    **kwargs
                )

                if res.status_code != 200:
                    print("HTTP status code: {0}".format(res.status_code))

                if int(res.status_code / 100) in [4, 5]:  # 4XX and 5XX codes
                    print("Waiting 10 second before retrying.")

                    retries += 1
                    if retries <= self.max_retries:
                        print(retries)
                        print("Waiting 10 second before retrying.")
                        time.sleep(10)
                        continue
                    else:
                        print("Maximum retries reached, skipping.")
                        return None
                else:
                    response_is_final = True
            except ConnectionError as e:
                print(url)

        return res
