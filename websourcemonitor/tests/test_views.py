from unittest.mock import patch

from django.test import TestCase, Client

from websourcemonitor.models import OrganisationType
from websourcemonitor.views import Content
from websourcemonitor.tests import parsed_content


class ViewTest(TestCase):

    def setUp(self):
        """
        create client_stub and a Content object
        containing a test which is different from the
        test parsed from the (mocked) live site
        :return:
        """
        super().setUp()
        self.client_stub = Client()

        self.org = OrganisationType.objects.create(
            name='Test'
        )
        Content.objects.create(
            title='Test1',
            organisation_type=self.org,
            url='http://istituzione.comune.test.it',
            op_url='http://politici.openpolis.it/istituzione/test/1',
            content=parsed_content[:-50]
        )

    @patch.object(Content, 'get_live_content')
    def test_view_diff_route_responds(self, mock_get_live_content):
        # stored content is different from modified content
        content = Content.objects.get(title="Test1")

        # Configure the mock to return the parsed content
        mock_get_live_content.return_value = (200, parsed_content)

        response = self.client_stub.get('/websourcemonitor/diff/{0}/'.format(content.pk))
        self.assertEquals(200, response.status_code)

    @patch.object(Content, 'get_live_content')
    def test_view_diff_route_contains_links(self, mock_get_live_content):
        # stored content is different from modified content
        content = Content.objects.get(title="Test1")

        # Configure the mock to return the parsed content
        mock_get_live_content.return_value = (200, parsed_content)

        response = self.client_stub.get('/websourcemonitor/diff/{0}/'.format(content.pk))
        self.assertIn(content.url, str(response.content))
        self.assertIn(content.op_url, str(response.content))

    # def test_view_signal_route(self):
    #     content = Content.objects.get(title="Test1")
    #
    #     response = self.client_stub.get('/signal/{0}'.format(content.pk))
    #     self.assertEquals(response.status_code, 200)
