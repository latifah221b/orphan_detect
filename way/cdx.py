from .session import Session
import logging
logger = logging.getLogger(__name__)

SEARCH_URL = "https://web.archive.org/cdx/search/cdx"

def search(url,
    from_date=None,
    to_date=None,
    uniques_only=True,
    collapse=None,
    session=None):

    session = session or Session()
    res = session.get(SEARCH_URL, params={
        "url": url,
        "from": from_date,
        "to": to_date,
        "showDupeCount": "true",
        "output": "json",
        "filter":"statuscode:200"
    })

    if res.status_code == 200:
        cdx = res.json()

    else:
        log_msg = 'CDX exception: "{0}"'
        logger.info(log_msg.format(
            res.content.decode("utf-8").strip()
        ))
        return []

    if len(cdx) < 2: return []
    fields = cdx[0]
    snapshots = [ dict(zip(fields, row)) for row in cdx[1:] ]

    if uniques_only:
        return [ s for s in snapshots if int(s["dupecount"]) == 0 ]
    else:
        return snapshots
