from unittest.mock import patch, Mock

from django.utils import timezone
from django.test import TestCase
import websourcemonitor
from websourcemonitor.models import Content, OrganisationType
from websourcemonitor.tests import html_content, parsed_content
from requests.exceptions import HTTPError


class ContentTests(TestCase):

    def setUp(self):
        """
        create contents and read html and parsed content used in tests
        :return:
        """
        self.org = OrganisationType.objects.create(
            name='Test'
        )
        Content.objects.create(
            title='Test1',
            organisation_type=self.org,
        )
        Content.objects.create(
            title='Test2',
            organisation_type=self.org,
            content='Test content',
            verification_status=Content.STATUS_ERROR,
            verification_error='Test error message',
            verified_at=timezone.now()
        )
        Content.objects.create(
            title='GC - 5132 - Roma (RM)',
            organisation_type=self.org,
            selector="//*[@id=\"wpsportletdx\"]/div[3]/div/div"
        )
        Content.objects.create(
            title='GC - 7228 - Enna (EN)',
            organisation_type=self.org,
            selector="//*[@class=\"contact-category\"]"
        )
        Content.objects.create(
            title='Giunta Comunale di Roma Capitale',
            organisation_type=self.org,
            selector="//*[@id=\"wpsportletdx\"]/div[3]/div/div"
        )
        self.mock_get_patcher = patch('websourcemonitor.utils.requests.Session.get')
        self.mock_get = self.mock_get_patcher.start()

    def tearDown(self):
        self.mock_get_patcher.stop()

    def test_created_content_should_have_null_values(self):
        """
        newly created content has null values
        """
        content = Content.objects.get(title='Test1')
        self.assertIsNone(content.content)
        self.assertIsNone(content.verification_status)
        self.assertIsNone(content.verification_error)
        self.assertIsNone(content.verified_at)

    def test_content_url_length_limit(self):
        """
        test that the url field can contain strings
        longer than the default limitations,
        but shorter than 1024
        """
        content = Content.objects.get(title='Test2')

        # test that urls shorter than 1024
        # characters are ok
        try:
            content.url = "x" * 1000
            content.save()
        except Exception as e:
            self.fail(
                "test_content_url_length_limit"
                "failed while trying to save "
                "a url 512 chars length. {0}".format(e)
            )

        # test that urls shorter than 1024
        # characters are not ok
        content.url = "x" * 1048
        self.assertRaises(Exception, content.save)

    def test_reset_should_set_values_to_null(self):
        """
        reset() sets content, verification_status,
        verification_error and verified_at to None
        """
        content = Content.objects.get(title='Test2')

        # reset values
        content.reset()

        self.assertIsNone(content.content)
        self.assertIsNone(content.verification_status)
        self.assertIsNone(content.verification_error)
        self.assertIsNone(content.verified_at)

    def test_get_live_content_when_response_is_ok(self):
        """
        when a remote source that responds with a 200 status codeis parsed,
        content is extracted correctly
        """
        content = Content.objects.get(title="GC - 5132 - Roma (RM)")

        self.mock_get.return_value.ok = True
        self.mock_get.return_value.status_code = 200
        self.mock_get.return_value.content = html_content

        # Call the service, which will send a request to the server.
        (resp_code, resp_content) = content.get_live_content()

        self.assertEqual(resp_code, 200)
        self.assertEqual(resp_content, parsed_content)

    def test_get_live_content_when_requests_raises_exception(self):
        """
        when a remote source responds with a status code != 200,
        the error code and the "URL" string are returned
        """
        content = Content.objects.get(title="GC - 5132 - Roma (RM)")

        # Configure the mock to return a response the ok attribute set to true
        self.mock_get.side_effect = ConnectionError('Boom')

        # Call the service, which will send a request to the server.
        (resp_code, resp_content) = content.get_live_content()

        self.assertEqual(resp_code, 910)
        self.assertEqual(str(resp_content), "Boom")

        # clears mock side effect
        self.mock_get.side_effect = None

    def test_get_live_content_when_response_status_code_is_not_200(self):
        """
        when a remote source responds with a status code != 200,
        the error code and the "URL" string are returned
        """
        content = Content.objects.get(title="GC - 5132 - Roma (RM)")

        # Configure the mock to return a response the ok attribute set to true
        expected = HTTPError(Mock(status=404), "Not found")
        self.mock_get.return_value.ok = False
        self.mock_get.return_value.status_code = 404
        self.mock_get.return_value.raise_for_status.side_effect = expected

        # Call the service, which will send a request to the server.
        (resp_code, resp_content) = content.get_live_content()

        self.assertEqual(resp_code, 404)
        self.assertEqual(resp_content, expected)

    def test_get_live_content_when_xpath_finds_nothing(self):
        """
        when a remote source does not contain meaningful content,
        then the tuple (900, "XPATH non trovato") is returned
        """
        content = Content.objects.get(title="GC - 5132 - Roma (RM)")
        content.xpath = "//*[@id=\"wpsportletdxxx\"]/div[3]/div/div"
        content.save()

        # Configure the mock to return a response the ok attribute set to true
        self.mock_get.return_value.ok = True
        self.mock_get.return_value.status_code = 200
        self.mock_get.return_value.content = html_content

        # Call the service, which will send a request to the server.
        (resp_code, resp_content) = content.get_live_content()

        self.assertEqual(resp_code, 900)
        self.assertEqual(resp_content, "XPATH non trovato")

    def test_get_live_content_when_xpath_syntax_wrong(self):
        """
        when a remote source does not contain meaningful content,
        then the tuple (901, "XPATH errore sintassi") is returned
        """
        content = Content.objects.get(title="GC - 5132 - Roma (RM)")
        content.xpath = "//*[#id=\"wpsportletdx\"]/div[3]/div/div"
        content.save()

        # Configure the mock to return a response the ok attribute set to true
        self.mock_get.return_value.ok = True
        self.mock_get.return_value.status_code = 200
        self.mock_get.return_value.content = html_content

        # Call the service, which will send a request to the server.
        (resp_code, resp_content) = content.get_live_content()

        self.assertEqual(resp_code, 901)
        self.assertEqual(resp_content, "XPATH errore sintassi: Invalid expression")

    def test_get_live_content_does_not_contain_js_or_css(self):
        """
        when a remote source that responds with a 200 status codeis parsed,
        extracted content does not contain javascript or css tags
        """
        with open(f'{websourcemonitor.__path__[0]}/tests/resources/source_enna_original.html', 'r') as src_f:
            html_enna_content = src_f.read().encode('utf8')
        with open(f'{websourcemonitor.__path__[0]}/tests/resources/source_parsed_enna_content.txt', 'r') as src_f:
            parsed_enna_content = src_f.read().strip()

        content = Content.objects.get(title="GC - 7228 - Enna (EN)")

        self.mock_get.return_value.ok = True
        self.mock_get.return_value.status_code = 200
        self.mock_get.return_value.content = html_enna_content

        # Call the service, which will send a request to the server.
        (resp_code, resp_content) = content.get_live_content()

        self.maxDiff = None
        self.assertEqual(resp_content, parsed_enna_content)

    @patch.object(Content, 'get_live_content')
    def test_verify_detect_changes_when_response_ok(self, mock_get_live_content):
        """
        verify set status to Content.STATUS_CHANGED when
        stored content is different from remote
        """
        # stored content is different from modified content
        content = Content.objects.get(title="GC - 5132 - Roma (RM)")
        content.content = parsed_content[:-50]
        content.save()

        # Configure the mock to return the parsed content
        mock_get_live_content.return_value = (200, parsed_content)

        # Call the service, which will send a request to the server.
        verification_status = content.verify()

        self.assertEqual(verification_status, Content.STATUS_CHANGED)
        self.assertIsNotNone(content.verified_at)

    @patch.object(Content, 'get_live_content')
    def test_verify_do_not_detect_changes_when_response_ok(self, mock_get_live_content):
        """
        verify set status to Content.STATUS_NOT_CHANGED when
        stored content is equal from remote
        """
        # stored content is different from modified content
        content = Content.objects.get(title="GC - 5132 - Roma (RM)")
        content.content = parsed_content
        content.save()

        # Configure the mock to return the parsed content
        mock_get_live_content.return_value = (200, parsed_content)

        # Call the service, which will send a request to the server.
        verification_status = content.verify()

        self.assertEqual(verification_status, Content.STATUS_NOT_CHANGED)
        self.assertIsNotNone(content.verified_at)

    @patch.object(Content, 'get_live_content')
    def test_verify_sets_verification_error_when_response_is_not_ok(self, mock_get_live_content):
        """
        verify set status to Content.STATUS_ERROR, and
        verification_error to ERRORE <CODE> (<MSG>), when
        some kind of errors appear
        """
        # stored content is different from modified content
        content = Content.objects.get(title="GC - 5132 - Roma (RM)")

        # Configure the mock to return the parsed content
        mock_get_live_content.return_value = (900, "XPATH non trovato")

        # Call the service, which will send a request to the server.
        _ = content.verify()

        self.assertEqual(content.verification_status, Content.STATUS_ERROR)
        self.assertEqual(content.verification_error, "ERRORE 900 (XPATH non trovato)")

    @patch.object(Content, 'get_live_content')
    def test_update_change_status_when_response_is_ok(self, mock_get_live_content):
        """
        update set status to Content.STATUS_UPDATED when
        stored content is equal from remote
        it also sets the content field to the remote content
        """
        # stored content is different from modified content
        content = Content.objects.get(title="GC - 5132 - Roma (RM)")
        content.content = ""
        content.verification_status = Content.STATUS_CHANGED
        content.verified_at = timezone.now()
        content.save()

        # Configure the mock to return the parsed content
        mock_get_live_content.return_value = (200, parsed_content)

        # Call the service, which will send a request to the server.
        _ = content.update()

        self.assertEqual(content.verification_status, Content.STATUS_UPDATED)
        self.assertEqual(content.content, parsed_content)
        self.assertIsNotNone(content.verified_at)
