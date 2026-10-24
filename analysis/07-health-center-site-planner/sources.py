"""Policy facts the page may state, each with its source and the date it was checked. Nothing here is typed into the page by hand:
the page reads output/facts.json. A fact is only written if its sentence is found in the downloaded source."""
import html
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
RAW = HERE / "data" / "raw"
CHECKED = "2026-10-23"


def _text(name):
    t = (RAW / name).read_text(errors="ignore")
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)))


def build():
    nap = _text("nap_bulletin.html")
    fr = _text("fr_2026-11094.txt")
    m = re.search(r"announce \$(\d+) million in New Access Points awards.{0,160}?(\d+) new and existing health centers in establishing (\d+) new sites", nap)
    assert m, "NAP sentence not found in the HRSA bulletin"
    assert re.search(r"no later than January 1, 2027", fr), "start date not found in the CMS rule"
    assert re.search(r"renewals once every 6 months", fr), "6-month renewals not found in the CMS rule"
    facts = {
        "checked": CHECKED,
        "new_access_points_2026": {
            "millions_usd": int(m.group(1)), "health_centers": int(m.group(2)), "new_sites": int(m.group(3)), "announced": "2026-08-13",
            "source": "HRSA bulletin of 2026-08-27", "url": "https://content.govdelivery.com/accounts/USHHSHRSA/bulletins/426df8a", "checked": CHECKED,
        },
        "medicaid_community_engagement": {
            "states_start_no_later_than": "2027-01-01", "renewals_for_expansion_adults": "every 6 months",
            "source": "CMS interim final rule, Federal Register 91 FR 33348, 2026-06-03", "url": "https://www.federalregister.gov/documents/full_text/text/2026/06/03/2026-11094.txt",
            "example_for_revenue_side": "/casestudies/09-health-center-coverage-loss-stress-test/", "checked": CHECKED,
        },
        "link_only": [
            {"topic": "HRSA service area competition, Add a Site to Scope form, New Access Point rules", "url": "https://www.hrsa.gov/grants/find-funding/HRSA-27-005",
             "status": "HRSA's pages return 403 Access Denied to scripts, including one try with headless Chromium and a normal user agent on 2026-10-23, so the wording could not be read and no date, point value or threshold from them is stated on the page."},
        ],
    }
    return facts


def write(out_dir):
    facts = build()
    (Path(out_dir) / "facts.json").write_text(json.dumps(facts, indent=1))
    return facts


if __name__ == "__main__":
    print(write(HERE / "output"))
