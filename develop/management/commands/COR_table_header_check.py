"""This command is used to query the APIs, compare the results with the DB and make appropriate changes."""
import logging
from bs4 import BeautifulSoup
import requests
import sys
from datetime import datetime
from prettytable import PrettyTable

from django.core.management.base import BaseCommand
from develop.models import *
from datetime import datetime

from .emails import *
logger = logging.getLogger("django")


def get_page_content(page_link):
    n = datetime.now()

    try:
        page_response = requests.get(page_link, timeout=10)
    except requests.exceptions.RequestException as e:
        print(n.strftime("%H:%M %m-%d-%y") + ": Connection problem to " + page_link)
        sys.exit(1)

    if page_response.status_code == 200:
        return BeautifulSoup(page_response.content, "html.parser")
    else:
        return None


class Command(BaseCommand):
    def handle(self, *args, **options):
        sr_page_link = "https://raleighnc.gov/services/zoning-planning-and-development/site-review-cases"
        zon_page_link = "https://raleighnc.gov/SupportPages/zoning-cases"
        tc_page_link = "https://raleighnc.gov/SupportPages/text-change-cases"
        neighbor_page_link = "https://raleighnc.gov/planning/neighborhood-meetings"
        message = ""

        # scrape the target websites and verify that the table headers are what we expect.

        # Site Review tables
        sr_expected = ["Case Number", "Project Name/Location/Description", "CAC", "Status*", "Contact"]
        sr_expected_2022 = ["Case Number", "Project Name/Location/Description", "Status*", "Contact"]
        sr_tables = get_page_content(sr_page_link).find_all("table")
        for sr_table in sr_tables:
            x = PrettyTable()
            sr_actual = []
            table_thead = sr_table.find("thead")
            thead_row = table_thead.find_all("th")
            if not thead_row:
                thead_row = table_thead.find_all("td")

            for header in thead_row:
                sr_actual.append(header.get_text().strip())

            if sr_actual == sr_expected or sr_actual == sr_expected_2022:
                pass
            else:
                message = "SR Table has changed.\n"
                try:
                    x.add_row(sr_actual)
                    x.add_row(sr_expected)
                    message += str(x)
                except Exception as e:
                    print(e)
                    message += "Problem with table. Please check site reviews."

        # AAD tables
        # aad_expected = ["Case Number", "Project Name/Location/Description", "Status*", "Contact"]
        # aad_tables = get_page_content(aad_page_link).find_all("table")
        # for aad_table in aad_tables:
        #     x = PrettyTable()
        #     aad_actual = []
        #     table_thead = aad_table.find("thead")
        #     thead_row = table_thead.find_all("td")
        #
        #     for header in thead_row:
        #         aad_actual.append(header.get_text().strip())
        #
        #     if aad_actual == aad_expected:
        #         pass
        #     else:
        #         message = "AAD Table has changed.\n"
        #         try:
        #             x.add_row(aad_actual)
        #             x.add_row(aad_expected)
        #             message += str(x)
        #         except Exception as e:
        #             print(e)
        #             message += "Problem with table. Please check AADs."

        # TCC tables
        tcc_expected = ["Case Number", "Project Name/Location/Description", "Description", "Status", "Contact"]
        tcc_tables = get_page_content(tc_page_link).find_all("table")
        for tcc_table in tcc_tables[:1]:
            x = PrettyTable()
            tcc_actual = []
            table_thead = tcc_table.find("thead")
            thead_row = table_thead.find_all("td")

            for header in thead_row:
                tcc_actual.append(header.get_text().strip())

            if len(tcc_actual) > 0:
                if tcc_actual == tcc_expected:
                    pass
                else:
                    message = "TCC Table has changed.\n"
                    try:
                        x.add_row(tcc_actual)
                        x.add_row(tcc_expected)
                        message += str(x)
                    except Exception as e:
                        print(e)
                        message += "Problem with table. Please check TCCs."

        # Zoning tables
        zon_expected = ["Case Number, Application & Status", "Location & Map Link", "Council District", "Staff Contact"]
        zon_tables = get_page_content(zon_page_link).find_all("table")
        # for zon_table in zon_tables:
        x = PrettyTable()
        zon_actual = []
        table_thead = zon_tables[0].find("thead")
        thead_row = table_thead.find_all("th")
        if not thead_row:
            thead_row = table_thead.find_all("td")

        for header in thead_row:
            zon_actual.append(header.get_text().strip().replace("\n", ""))

        if zon_actual == zon_expected:
            pass
        else:
            try:
                x.add_row(zon_actual)
                x.add_row(zon_expected)
                message = "Zon Table has changed.\n"
                message += str(x)
            except Exception as e:
                print(e)
                message += "Problem with table. Please check zoning."

        # Neighborhood meetings tables
        # neighbor_expected = ["Meeting Details", "Rezoning Site Address", "Applicant/Link to Meeting Information",
        #                      "Council District", "Staff Contact"]
        neighbor_expected = ['Date & Time', 'Meeting Location', 'Site Location & Map', 'Request',
                                                 'Council District', 'Applicant Contact', 'Staff Contact']
        neighbor_tables = get_page_content(neighbor_page_link).find_all("table")
        for count, neighbor_table in enumerate(neighbor_tables):
            # June 2, 22: It's a table inside a table. So skip the first one. :(
            if count == 0:
                continue

            x = PrettyTable()
            neighbor_actual = []
            # thead_row = neighbor_table.find_all("tr")[0]
            thead_row = neighbor_table.find("thead")
            thead_row_items = thead_row.find_all("th")

            for header in thead_row_items:
                neighbor_actual.append(header.get_text().strip().replace("\n", ""))

            if neighbor_actual == neighbor_expected:
                pass
            else:
                try:
                    print(neighbor_actual)
                    # print(neighbor_expected)
                    x.add_row(neighbor_actual)
                    x.add_row(neighbor_expected)
                    message = "Neighborhood Table has changed.\n"
                    message += str(x)
                except Exception as e:
                    print(e)
                    message += "Problem with neighborhood tables, please check."

        # DA case tables
        # da_expected = ["Case Number", "Project Name/Location/Description", "Status*", "Contact"]
        # da_tables = get_page_content(da_page_link).find_all("table")
        # for da_table in da_tables:
        #     x = PrettyTable()
        #     da_actual = []
        #     table_thead = da_table.find("thead")
        #     thead_row = table_thead.find_all("td")
        #
        #     for header in thead_row:
        #         da_actual.append(header.get_text().strip())
        #
        #     if da_actual == da_expected:
        #         pass
        #     else:
        #         try:
        #             x.add_row(da_actual)
        #             x.add_row(da_expected)
        #             message = "DA Case Table has changed.\n"
        #             message += str(x)
        #         except Exception as e:
        #             print(e)
        #             message += "Problem with da case tables, please check."

        if message:
            send_email_notice(message, email_admins())
