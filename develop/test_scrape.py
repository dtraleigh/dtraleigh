from bs4 import BeautifulSoup
from unittest.mock import patch, MagicMock

from django.test import SimpleTestCase
from django.test import TestCase
from develop.management.commands.scrape import *


class ScrapeTestCaseSimple(SimpleTestCase):
    def test_get_page_content(self):
        """quick test to check that the sites we are scraping are returning data"""
        websites_used = [
            "https://raleighnc.gov/services/zoning-planning-and-development/site-review-cases",
            # "https://raleighnc.gov/SupportPages/administrative-alternate-design-cases",
            "https://raleighnc.gov/planning/services/rezoning-process/rezoning-cases",
            "https://raleighnc.gov/planning/services/text-changes/text-change-cases",
            ]

        for url in websites_used:
            self.assertIsNotNone(get_page_content(url))

    def test_get_rows_in_table(self):
        """get_rows_in_table() takes in an html table and returns
        a list of the rows. Test that we get back the correct number of rows from the table."""

        # Check one random sample from SRs
        sr_table = """<table><thead><tr><td><strong>Case Number</strong></td>
        <td><strong>Project Name/Location/Description</strong></td>
        <td><strong>CAC</strong></td>
        <td><strong>Status*</strong></td>
        <td><strong>Contact</strong></td>
        </tr></thead><tbody><tr><td><a href="https://cityofraleigh0drupal.blob.core.usgovcloudapi.net/drupal-prod/COR15/ASR-0001-2020.pdf">ASR-0001-2020</a></td>
        <td>Brier Creek Apartments/ 3900, 3910, 3920 and 3930 Macaw St/ apartments</td>
        <td>Northwest</td>
        <td>UR</td>
        <td><a href="/directory?action=search&amp;firstName=Michael&amp;lastName=Walters">Walters</a></td>
        </tr><tr><td><a href="https://cityofraleigh0drupal.blob.core.usgovcloudapi.net/drupal-prod/COR15/ASR-0002-2020.pdf">ASR-0002-2020</a></td>
        <td>Iglesia De Dios Pentecostal/ 4508 Old Poole Rd/ church</td>
        <td>Southeast</td>
        <td>UR</td>
        <td><a href="/directory?action=search&amp;firstName=Kasey&amp;lastName=Evans">Evans</a></td>
        </tr><tr><td><a href="https://cityofraleigh0drupal.blob.core.usgovcloudapi.net/drupal-prod/COR15/SR-106-17.pdf">SR-106-17</a></td>
        <td>Wakefield United Methodist/ 11001 Forest Pines Dr/ Place of Worship</td>
        <td>North</td>
        <td>UR</td>
        <td><a href="/directory?action=search&amp;firstName=Michael&amp;lastName=Walters">Walters</a></td>
        </tr></tbody></table>"""
        sr_souped = BeautifulSoup(sr_table, "html.parser")

        self.assertEqual(len(get_rows_in_table(sr_souped, "test")), 3)

    def test_get_case_number_from_row(self):
        """get_case_number_from_row() takes in a a list of all <td> tags that were in that <tr>"""
        sr_tds1 = """<td><a href="https://cityofraleigh0drupal.blob.core.usgovcloudapi.net/drupal-prod/COR15/SR-106-17.pdf">SR-106-17</a></td>, <td>Wakefield United Methodist/ 11001 Forest Pines Dr/ Place of Worship</td>, <td>North</td>, <td>UR</td>, <td><a href="/directory?action=search&amp;firstName=Michael&amp;lastName=Walters">Walters</a></td>"""
        tds_souped = BeautifulSoup(sr_tds1, "html.parser")
        row_tds = tds_souped.find_all("td")

        self.assertEqual(get_case_number_from_row(row_tds), "SR-106-17")

        sr_tds2 = """<td>SR-106-17</td>, <td>Wakefield United Methodist/ 11001 Forest Pines Dr/ Place of Worship</td>, <td>North</td>, <td>UR</td>, <td><a href="/directory?action=search&amp;firstName=Michael&amp;lastName=Walters">Walters</a></td>"""
        tds_souped = BeautifulSoup(sr_tds1, "html.parser")
        row_tds = tds_souped.find_all("td")

        self.assertEqual(get_case_number_from_row(row_tds), "SR-106-17")

    def test_get_generic_link(self):
        content1 = """<td><a href="https://cityofraleigh0drupal.blob.core.usgovcloudapi.net/drupal-prod/COR15/SR-106-17.pdf">SR-106-17</a></td>"""
        content1_souped = BeautifulSoup(content1, "html.parser")

        self.assertEqual(get_generic_link(content1_souped), "https://cityofraleigh0drupal.blob.core.usgovcloudapi.net/drupal-prod/COR15/SR-106-17.pdf")

        content2 = """<td><a href="https://cityofraleigh0drupal.blob.core.usgovcloudapi.net/drupal prod/COR15/SR 106 17.pdf">SR-106-17</a></td>"""
        content2_souped = BeautifulSoup(content2, "html.parser")

        self.assertEqual(get_generic_link(content2_souped), "https://cityofraleigh0drupal.blob.core.usgovcloudapi.net/drupal%20prod/COR15/SR%20106%2017.pdf")

        content3 = """<td>SR-106-17</td>"""
        content3_souped = BeautifulSoup(content3, "html.parser")

        self.assertEqual(get_generic_link(content3_souped), None)

    def test_extract_case_number_and_year(self):
        """Test extraction of zpnum and zpyear from case number text"""
        # Standard format
        zpnum, zpyear = extract_case_number_and_year("Z-1234-23")
        self.assertEqual(zpnum, "1234")
        self.assertEqual(zpyear, "2023")

        # With different year
        zpnum, zpyear = extract_case_number_and_year("Z-5678-24")
        self.assertEqual(zpnum, "5678")
        self.assertEqual(zpyear, "2024")

    def test_extract_case_number_text(self):
        """Test extraction of case number text from table cell"""
        # Case with text on first line
        html1 = """<td>Z-1234-23\n<strong>Status</strong></td>"""
        souped1 = BeautifulSoup(html1, "html.parser")
        td1 = souped1.find("td")
        self.assertEqual(extract_case_number_text(td1), "Z-1234-23")

        # Case with p tag (text on second line)
        html2 = """<td><p></p>\nZ-5678-24</td>"""
        souped2 = BeautifulSoup(html2, "html.parser")
        td2 = souped2.find("td")
        self.assertEqual(extract_case_number_text(td2), "Z-5678-24")

        # Real example
        html3 = """<td><p><a href="https://pub-raleighnc.escribemeetings.com/Meeting.aspx?Id=b4408476-db58-47ea-83ee-0b75a5e9dced&amp;lang=English&amp;Agenda=Agenda&amp;Item=2208&amp;Tab=attachments" class="ext" data-extlink="" target="_blank" rel="noopener nofollow" title="(opens in a new window)" data-uw-rm-brl="PR" data-uw-original-href="https://pub-raleighnc.escribemeetings.com/Meeting.aspx?Id=b4408476-db58-47ea-83ee-0b75a5e9dced&amp;lang=English&amp;Agenda=Agenda&amp;Item=2208&amp;Tab=attachments" aria-label="Z-70-22 - open in a new tab" data-uw-rm-ext-link="" uw-rm-external-link-id="https://pub-raleighnc.escribemeetings.com/meeting.aspx?id=b4408476-db58-47ea-83ee-0b75a5e9dced&amp;lang=english&amp;agenda=agenda&amp;item=2208&amp;tab=attachments$z-70-22" style="transition: all;">Z-70-22<svg focusable="false" width="1em" height="1em" class="ext" data-extlink-placement="append" aria-label="(link is external)" viewBox="0 0 80 40" role="img" aria-hidden="false"><title>(link is external)</title><path d="M48 26c-1.1 0-2 0.9-2 2v26H10V18h26c1.1 0 2-0.9 2-2s-0.9-2-2-2H8c-1.1 0-2 0.9-2 2v40c0 1.1 0.9 2 2 2h40c1.1 0 2-0.9 2-2V28C50 26.9 49.1 26 48 26z"></path><path d="M56 6H44c-1.1 0-2 0.9-2 2s0.9 2 2 2h7.2L30.6 30.6c-0.8 0.8-0.8 2 0 2.8C31 33.8 31.5 34 32 34s1-0.2 1.4-0.6L54 12.8V20c0 1.1 0.9 2 2 2s2-0.9 2-2V8C58 6.9 57.1 6 56 6z"></path></svg></a></p><p>Approved 09/16/25</p></td>"""
        souped3 = BeautifulSoup(html3, "html.parser")
        td3 = souped3.find("td")
        self.assertEqual(extract_case_number_text(td3), "Z-70-22")

        # Real example with link to text change
        html4 = """<td><p><a href="https://pub-raleighnc.escribemeetings.com/Meeting.aspx?Id=b6feb6bc-29c3-4f40-99dc-0b2d5c93f159&amp;lang=English&amp;Agenda=Agenda&amp;Item=3223&amp;Tab=attachments" class="ext" data-extlink="" target="_blank" rel="noopener nofollow" title="(opens in a new window)" data-uw-rm-brl="PR" data-uw-original-href="https://pub-raleighnc.escribemeetings.com/Meeting.aspx?Id=b6feb6bc-29c3-4f40-99dc-0b2d5c93f159&amp;lang=English&amp;Agenda=Agenda&amp;Item=3223&amp;Tab=attachments" aria-label="Z-13-25 (TCZ-13-25) - open in a new tab" data-uw-rm-ext-link="" uw-rm-external-link-id="https://pub-raleighnc.escribemeetings.com/meeting.aspx?id=b6feb6bc-29c3-4f40-99dc-0b2d5c93f159&amp;lang=english&amp;agenda=agenda&amp;item=3223&amp;tab=attachments$z-13-25(tcz-13-25)">Z-13-25 (TCZ-13-25)&nbsp;<svg focusable="false" width="1em" height="1em" class="ext" data-extlink-placement="append" aria-label="(link is external)" viewBox="0 0 80 40" role="img" aria-hidden="false"><title>(link is external)</title><path d="M48 26c-1.1 0-2 0.9-2 2v26H10V18h26c1.1 0 2-0.9 2-2s-0.9-2-2-2H8c-1.1 0-2 0.9-2 2v40c0 1.1 0.9 2 2 2h40c1.1 0 2-0.9 2-2V28C50 26.9 49.1 26 48 26z"></path><path d="M56 6H44c-1.1 0-2 0.9-2 2s0.9 2 2 2h7.2L30.6 30.6c-0.8 0.8-0.8 2 0 2.8C31 33.8 31.5 34 32 34s1-0.2 1.4-0.6L54 12.8V20c0 1.1 0.9 2 2 2s2-0.9 2-2V8C58 6.9 57.1 6 56 6z"></path></svg></a></p><p>Approved 11/04/25&nbsp;</p></td>"""
        souped4 = BeautifulSoup(html4, "html.parser")
        td4 = souped4.find("td")
        self.assertEqual(extract_case_number_text(td4), "Z-13-25")

    def test_extract_status_from_same_cell(self):
        """Test extraction of status when it's in the same cell"""
        html1 = """<td>Z-1234-23\nApproved</td>"""
        souped1 = BeautifulSoup(html1, "html.parser")
        td1 = souped1.find("td")

        status1 = extract_status(td1, 0, [])
        self.assertEqual(status1, "Approved")

        # Real example
        html2 = """<td><p><a href="https://pub-raleighnc.escribemeetings.com/Meeting.aspx?Id=b4408476-db58-47ea-83ee-0b75a5e9dced&amp;lang=English&amp;Agenda=Agenda&amp;Item=2208&amp;Tab=attachments" class="ext" data-extlink="" target="_blank" rel="noopener nofollow" title="(opens in a new window)" data-uw-rm-brl="PR" data-uw-original-href="https://pub-raleighnc.escribemeetings.com/Meeting.aspx?Id=b4408476-db58-47ea-83ee-0b75a5e9dced&amp;lang=English&amp;Agenda=Agenda&amp;Item=2208&amp;Tab=attachments" aria-label="Z-70-22 - open in a new tab" data-uw-rm-ext-link="" uw-rm-external-link-id="https://pub-raleighnc.escribemeetings.com/meeting.aspx?id=b4408476-db58-47ea-83ee-0b75a5e9dced&amp;lang=english&amp;agenda=agenda&amp;item=2208&amp;tab=attachments$z-70-22" style="transition: all;">Z-70-22<svg focusable="false" width="1em" height="1em" class="ext" data-extlink-placement="append" aria-label="(link is external)" viewBox="0 0 80 40" role="img" aria-hidden="false"><title>(link is external)</title><path d="M48 26c-1.1 0-2 0.9-2 2v26H10V18h26c1.1 0 2-0.9 2-2s-0.9-2-2-2H8c-1.1 0-2 0.9-2 2v40c0 1.1 0.9 2 2 2h40c1.1 0 2-0.9 2-2V28C50 26.9 49.1 26 48 26z"></path><path d="M56 6H44c-1.1 0-2 0.9-2 2s0.9 2 2 2h7.2L30.6 30.6c-0.8 0.8-0.8 2 0 2.8C31 33.8 31.5 34 32 34s1-0.2 1.4-0.6L54 12.8V20c0 1.1 0.9 2 2 2s2-0.9 2-2V8C58 6.9 57.1 6 56 6z"></path></svg></a></p><p>Approved 09/16/25</p></td>"""
        souped2 = BeautifulSoup(html2, "html.parser")
        td2 = souped2.find("td")

        status2 = extract_status(td2, 0, [])
        self.assertEqual(status2, "Approved 09/16/25")

        # Real example with link to text change
        html3 = """<td><p><a href="https://pub-raleighnc.escribemeetings.com/Meeting.aspx?Id=b6feb6bc-29c3-4f40-99dc-0b2d5c93f159&amp;lang=English&amp;Agenda=Agenda&amp;Item=3223&amp;Tab=attachments" class="ext" data-extlink="" target="_blank" rel="noopener nofollow" title="(opens in a new window)" data-uw-rm-brl="PR" data-uw-original-href="https://pub-raleighnc.escribemeetings.com/Meeting.aspx?Id=b6feb6bc-29c3-4f40-99dc-0b2d5c93f159&amp;lang=English&amp;Agenda=Agenda&amp;Item=3223&amp;Tab=attachments" aria-label="Z-13-25 (TCZ-13-25) - open in a new tab" data-uw-rm-ext-link="" uw-rm-external-link-id="https://pub-raleighnc.escribemeetings.com/meeting.aspx?id=b6feb6bc-29c3-4f40-99dc-0b2d5c93f159&amp;lang=english&amp;agenda=agenda&amp;item=3223&amp;tab=attachments$z-13-25(tcz-13-25)">Z-13-25 (TCZ-13-25)&nbsp;<svg focusable="false" width="1em" height="1em" class="ext" data-extlink-placement="append" aria-label="(link is external)" viewBox="0 0 80 40" role="img" aria-hidden="false"><title>(link is external)</title><path d="M48 26c-1.1 0-2 0.9-2 2v26H10V18h26c1.1 0 2-0.9 2-2s-0.9-2-2-2H8c-1.1 0-2 0.9-2 2v40c0 1.1 0.9 2 2 2h40c1.1 0 2-0.9 2-2V28C50 26.9 49.1 26 48 26z"></path><path d="M56 6H44c-1.1 0-2 0.9-2 2s0.9 2 2 2h7.2L30.6 30.6c-0.8 0.8-0.8 2 0 2.8C31 33.8 31.5 34 32 34s1-0.2 1.4-0.6L54 12.8V20c0 1.1 0.9 2 2 2s2-0.9 2-2V8C58 6.9 57.1 6 56 6z"></path></svg></a></p><p>Approved 11/04/25&nbsp;</p></td>"""
        souped3 = BeautifulSoup(html3, "html.parser")
        td3 = souped3.find("td")

        status3 = extract_status(td3, 0, [])
        self.assertEqual(status3, "Approved 11/04/25")

        # Real example with status on two lines
        html4 = """<td><p><a href="https://cityofraleigh0drupal.blob.core.usgovcloudapi.net/drupal-prod/COR22/Z-040-25.pdf" data-uw-pdf-br="2" data-uw-pdf-doc="">Z-40-25</a></p><p>Second Neighborhood Meeting Required&nbsp;</p></td>"""
        souped4 = BeautifulSoup(html4, "html.parser")
        td4 = souped4.find("td")

        status4 = extract_status(td4, 0, [])
        self.assertEqual(status4, "Second Neighborhood Meeting Required")

    def test_validate_scraped_row_valid(self):
        """Test validation passes with all fields present"""
        result = validate_scraped_row("Z-1234-23", "123 Main St", "Z-1234-23", "Approved")
        self.assertTrue(result)

    def test_validate_scraped_row_invalid(self):
        """Test validation fails with missing fields"""
        # Missing case number
        result = validate_scraped_row("", "123 Main St", "Z-1234-23", "Approved")
        self.assertFalse(result)

        # Missing location
        result = validate_scraped_row("Z-1234-23", "", "Z-1234-23", "Approved")
        self.assertFalse(result)

        # Missing zoning case
        result = validate_scraped_row("Z-1234-23", "123 Main St", "", "Approved")
        self.assertFalse(result)

        # Missing status
        result = validate_scraped_row("Z-1234-23", "123 Main St", "Z-1234-23", "")
        self.assertFalse(result)

    def test_process_zoning_row_valid(self):
        """Test processing valid zoning rows. html was pulled on Nov 28, 2025 and only contains the top 4 rows with some custom mods. (removed header row)"""
        html = """<table class="table tablesaw tablesaw-swipe" data-tablesaw-minimap="" data-tablesaw-mode-switch="" data-tablesaw-mode="swipe" id="tablesaw-8459" style=""><tbody><tr><td><p><a href="https://pub-raleighnc.escribemeetings.com/Meeting.aspx?Id=b4408476-db58-47ea-83ee-0b75a5e9dced&amp;lang=English&amp;Agenda=Agenda&amp;Item=2208&amp;Tab=attachments" class="ext" data-extlink="" target="_blank" rel="noopener nofollow" title="(opens in a new window)" data-uw-rm-brl="PR" data-uw-original-href="https://pub-raleighnc.escribemeetings.com/Meeting.aspx?Id=b4408476-db58-47ea-83ee-0b75a5e9dced&amp;lang=English&amp;Agenda=Agenda&amp;Item=2208&amp;Tab=attachments" aria-label="Z-70-22 - open in a new tab" data-uw-rm-ext-link="" uw-rm-external-link-id="https://pub-raleighnc.escribemeetings.com/meeting.aspx?id=b4408476-db58-47ea-83ee-0b75a5e9dced&amp;lang=english&amp;agenda=agenda&amp;item=2208&amp;tab=attachments$z-70-22" style="transition: all;">Z-70-22<svg focusable="false" width="1em" height="1em" class="ext" data-extlink-placement="append" aria-label="(link is external)" viewBox="0 0 80 40" role="img" aria-hidden="false"><title>(link is external)</title><path d="M48 26c-1.1 0-2 0.9-2 2v26H10V18h26c1.1 0 2-0.9 2-2s-0.9-2-2-2H8c-1.1 0-2 0.9-2 2v40c0 1.1 0.9 2 2 2h40c1.1 0 2-0.9 2-2V28C50 26.9 49.1 26 48 26z"></path><path d="M56 6H44c-1.1 0-2 0.9-2 2s0.9 2 2 2h7.2L30.6 30.6c-0.8 0.8-0.8 2 0 2.8C31 33.8 31.5 34 32 34s1-0.2 1.4-0.6L54 12.8V20c0 1.1 0.9 2 2 2s2-0.9 2-2V8C58 6.9 57.1 6 56 6z"></path></svg></a></p><p>Approved 09/16/25</p></td><td><a href="https://maps.raleighnc.gov/imaps/?pin=0777935542,0777937355,0777932734" data-uw-rm-brl="PR" data-uw-original-href="https://maps.raleighnc.gov/imaps/?pin=0777935542,0777937355,0777932734">8151 Glenwood Ave, 6805 Lake Anne Dr, and&nbsp;8265 Winchester Dr</a></td><td><a href="https://raleighnc.gov/city-council/christina-jones" data-uw-rm-brl="PR" data-uw-original-href="https://raleighnc.gov/city-council/christina-jones">E</a></td><td><a href="/directory?action=search&amp;firstName=Hannah&amp;lastName=Reckhow" data-uw-rm-brl="PR" data-uw-original-href="/directory?action=search&amp;firstName=Hannah&amp;lastName=Reckhow">Reckhow</a></td></tr><tr><td><p><a href="https://cityofraleigh0drupal.blob.core.usgovcloudapi.net/drupal-prod/COR22/Z-012-23.pdf" data-uw-pdf-br="2" data-uw-pdf-doc="">Z-12-23</a></p><p>Additional Materials Required</p></td><td><a href="https://maps.raleighnc.gov/imaps/?pin=1712963537,1712955431" data-uw-rm-brl="PR" data-uw-original-href="https://maps.raleighnc.gov/imaps/?pin=1712963537,1712955431">3000 &amp; 3010 Rock Quarry Rd</a></td><td><a href="https://raleighnc.gov/city-council/corey-branch" data-uw-rm-brl="PR" data-uw-original-href="https://raleighnc.gov/city-council/corey-branch">C</a></td><td><a href="https://raleighnc.gov/directory?action=search&amp;firstName=Matthew&amp;lastName=Burns" data-uw-rm-brl="PR" data-uw-original-href="https://raleighnc.gov/directory?action=search&amp;firstName=Matthew&amp;lastName=Burns">Burns</a></td></tr><tr><td><p><a href="https://cityofraleigh0drupal.blob.core.usgovcloudapi.net/drupal-prod/COR22/Z-022-24.pdf" data-uw-pdf-br="2" data-uw-pdf-doc="">Z-22-24</a></p><p>Additional Materials Required</p></td><td><a href="https://maps.raleighnc.gov/imaps/?pin=1703743741,1703743643,1703743537,1703743439,1703743420,1703742754,1703742649,1703742644,1703742548,1703742543,1703742448,1703744663,1703744576,1703744469,1703744389" data-uw-rm-brl="PR" data-uw-original-href="https://maps.raleighnc.gov/imaps/?pin=1703743741,1703743643,1703743537,1703743439,1703743420,1703742754,1703742649,1703742644,1703742548,1703742543,1703742448,1703744663,1703744576,1703744469,1703744389">Wilmington Street Assemblage</a></td><td><a href="https://raleighnc.gov/city-council/corey-branch" data-uw-rm-brl="PR" data-uw-original-href="https://raleighnc.gov/city-council/corey-branch">C</a></td><td><a href="https://raleighnc.gov/directory?action=search&amp;firstName=Matthew&amp;lastName=Burns" data-uw-rm-brl="PR" data-uw-original-href="https://raleighnc.gov/directory?action=search&amp;firstName=Matthew&amp;lastName=Burns">Burns</a></td></tr><tr><td><p><a href="https://pub-raleighnc.escribemeetings.com/Meeting.aspx?Id=7db02dc5-3b2b-4406-b6ab-1596ecdb836d&amp;lang=English&amp;Agenda=Agenda&amp;Item=1892&amp;Tab=attachments" class="ext" data-extlink="" target="_blank" rel="noopener nofollow" title="(opens in a new window)" data-uw-rm-brl="PR" data-uw-original-href="https://pub-raleighnc.escribemeetings.com/Meeting.aspx?Id=7db02dc5-3b2b-4406-b6ab-1596ecdb836d&amp;lang=English&amp;Agenda=Agenda&amp;Item=1892&amp;Tab=attachments" aria-label="Z-48-24 - open in a new tab" data-uw-rm-ext-link="" uw-rm-external-link-id="https://pub-raleighnc.escribemeetings.com/meeting.aspx?id=7db02dc5-3b2b-4406-b6ab-1596ecdb836d&amp;lang=english&amp;agenda=agenda&amp;item=1892&amp;tab=attachments$z-48-24">Z-48-24<svg focusable="false" width="1em" height="1em" class="ext" data-extlink-placement="append" aria-label="(link is external)" viewBox="0 0 80 40" role="img" aria-hidden="false"><title>(link is external)</title><path d="M48 26c-1.1 0-2 0.9-2 2v26H10V18h26c1.1 0 2-0.9 2-2s-0.9-2-2-2H8c-1.1 0-2 0.9-2 2v40c0 1.1 0.9 2 2 2h40c1.1 0 2-0.9 2-2V28C50 26.9 49.1 26 48 26z"></path><path d="M56 6H44c-1.1 0-2 0.9-2 2s0.9 2 2 2h7.2L30.6 30.6c-0.8 0.8-0.8 2 0 2.8C31 33.8 31.5 34 32 34s1-0.2 1.4-0.6L54 12.8V20c0 1.1 0.9 2 2 2s2-0.9 2-2V8C58 6.9 57.1 6 56 6z"></path></svg></a></p><p>Approved 08/19/25</p></td><td><a href="https://maps.raleighnc.gov/imaps/?pin=1714392627,1714395527" data-uw-rm-brl="PR" data-uw-original-href="https://maps.raleighnc.gov/imaps/?pin=1714392627,1714395527">1220 &amp; 1246 Wicker Dr</a></td><td>ETJ</td><td>Klinger</td></tr></tbody></table>"""

        expecteds = [[2022, 70, "Approved 09/16/25", "8151 Glenwood Ave, 6805 Lake Anne Dr, and 8265 Winchester Dr"],
                     [2023, 12, "Additional Materials Required", "3000 & 3010 Rock Quarry Rd"],
                     [2024, 22, "Additional Materials Required", "Wilmington Street Assemblage"],
                     [2024, 48, "Approved 08/19/25","1220 & 1246 Wicker Dr"]]

        souped = BeautifulSoup(html, "html.parser")
        rows = souped.find_all("tr")

        for counter, (row, expected) in enumerate(zip(rows, expecteds)):
            with patch('develop.management.commands.scrape.get_generic_link') as mock_link:
                mock_link.side_effect = ["plan.pdf", "loc.html"]
                result = process_zoning_row(row, counter, [row])

            self.assertIsNotNone(result)
            self.assertEqual(result["zpyear"], expected[0])
            self.assertEqual(result["zpnum"], expected[1])
            self.assertEqual(result["status"], expected[2])
            self.assertEqual(result["location"], expected[3])

    def test_process_zoning_row_empty_district(self):
        """Test that row with empty council district is skipped"""
        html = """<table class="table tablesaw tablesaw-swipe" data-tablesaw-minimap="" data-tablesaw-mode-switch="" data-tablesaw-mode="swipe" id="tablesaw-8459" style=""><tbody><tr><td><p><a href="https://pub-raleighnc.escribemeetings.com/Meeting.aspx?Id=54d98e68-c62f-4bcc-94c2-71764cff5b4a&amp;lang=English&amp;Agenda=Agenda&amp;Item=3194&amp;Tab=attachments" class="ext" data-extlink="" target="_blank" rel="noopener nofollow" title="(opens in a new window)" data-uw-rm-brl="PR" data-uw-original-href="https://pub-raleighnc.escribemeetings.com/Meeting.aspx?Id=54d98e68-c62f-4bcc-94c2-71764cff5b4a&amp;lang=English&amp;Agenda=Agenda&amp;Item=3194&amp;Tab=attachments" aria-label="Z-13-24 - open in a new tab" data-uw-rm-ext-link="" uw-rm-external-link-id="https://pub-raleighnc.escribemeetings.com/meeting.aspx?id=54d98e68-c62f-4bcc-94c2-71764cff5b4a&amp;lang=english&amp;agenda=agenda&amp;item=3194&amp;tab=attachments$z-13-24">Z-13-24<svg focusable="false" width="1em" height="1em" class="ext" data-extlink-placement="append" aria-label="(link is external)" viewBox="0 0 80 40" role="img" aria-hidden="false"><title>(link is external)</title><path d="M48 26c-1.1 0-2 0.9-2 2v26H10V18h26c1.1 0 2-0.9 2-2s-0.9-2-2-2H8c-1.1 0-2 0.9-2 2v40c0 1.1 0.9 2 2 2h40c1.1 0 2-0.9 2-2V28C50 26.9 49.1 26 48 26z"></path><path d="M56 6H44c-1.1 0-2 0.9-2 2s0.9 2 2 2h7.2L30.6 30.6c-0.8 0.8-0.8 2 0 2.8C31 33.8 31.5 34 32 34s1-0.2 1.4-0.6L54 12.8V20c0 1.1 0.9 2 2 2s2-0.9 2-2V8C58 6.9 57.1 6 56 6z"></path></svg></a></p><p>Approved 10/21/25</p></td><td><a href="https://maps.raleighnc.gov/imaps/?pin=1722985060" data-uw-rm-brl="PR" data-uw-original-href="https://maps.raleighnc.gov/imaps/?pin=1722985060">1811 S New Hope Rd</a></td><td></td><td>Klinger&nbsp;</td></tr></tbody></table>"""

        souped = BeautifulSoup(html, "html.parser")
        row = souped.find("tr")

        result = process_zoning_row(row, 0, [row])

        self.assertIsNone(result)


class ScrapeTestCaseDjango(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Need to create 3 items to check against"""
        SiteReviewCase.objects.create(case_number="Test-SR-2020",
                                      project_name="Test SR Project")
        AdministrativeAlternate.objects.create(case_number="Test-AAD-2020",
                                               project_name="Test AAD Project")
        TextChangeCase.objects.create(case_number="Test-TCC-2020",
                                      project_name="Test TCC project")

    def test_determine_if_known_case2(self):
        """Happy, easy match"""
        known_sr_cases = SiteReviewCase.objects.all()
        sr1 = determine_if_known_case(known_sr_cases, "Test-SR-2020", "Test SR Project")
        self.assertEqual(sr1, known_sr_cases[0])

        known_aad_cases = AdministrativeAlternate.objects.all()
        aad1 = determine_if_known_case(known_aad_cases, "Test-AAD-2020", "Test AAD Project")
        self.assertEqual(aad1, known_aad_cases[0])

        known_tcc_cases = TextChangeCase.objects.all()
        tcc1 = determine_if_known_case(known_tcc_cases, "Test-TCC-2020", "Test TCC Project")
        self.assertEqual(tcc1, known_tcc_cases[0])

        # Very different matches
        known_sr_cases = SiteReviewCase.objects.all()
        sr2 = determine_if_known_case(known_sr_cases, "Wrong-SR-2020", "Wrong SR Project")
        self.assertEqual(sr2, None)

        known_aad_cases = AdministrativeAlternate.objects.all()
        aad2 = determine_if_known_case(known_aad_cases, "Wrong-AAD-2020", "Wrong AAD Project")
        self.assertEqual(aad2, None)

        known_tcc_cases = TextChangeCase.objects.all()
        tcc2 = determine_if_known_case(known_tcc_cases, "Wrong-TCC-2020", "Wrong TCC Project")
        self.assertEqual(tcc2, None)
