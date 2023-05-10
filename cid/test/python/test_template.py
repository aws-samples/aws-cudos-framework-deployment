import unittest

from cid.helpers.template import render_from_template
from cid.exceptions import CidCritical

class TestRenderFromTemplate(unittest.TestCase):
    def test_success_scenario(self):
        '''It is expected that template is properly renderred'''
        params = {
            "athena_datasource_arn": "some:datasource:arn",
            "athena_database_name": "cid_cur",
            "input_columns": [
                {"name": "billing_period", "type":"DATETIME"},
                {"name": "purchase_option", "type":"STRING"},
                {"name": "product_to_location", "type":"STRING"}
            ]
        }
        template_file = {}
        expected_result = {}
        with open('cid/test/files/example_view_template.json') as template_file_:
            template_file = template_file_.read()
        with open('cid/test/files/example_view_rendered.json') as expected_result_:
            expected_result = expected_result_.read()
        self.assertEqual(render_from_template(template_file,params),expected_result)

    def test_missing_parameter(self):
        '''Should throw error with missing parameter'''
        params = {
            "athena_datasource_arn": "some:datasource:arn",
            "input_columns": [
                {"name": "billing_period", "type":"DATETIME"},
            ]
        }
        source = {}
        outcome = {}
        with open('cid/test/files/example_view_template.json') as source_:
            source = source_.read()
        with self.assertRaises(CidCritical) as context:
            render_from_template(source,params)
        self.assertTrue("NameError: 'athena_database_name' is not defined" in str(context.exception))

    def test_invalid_options_type(self):
        '''Providing wrong parameter type'''
        with self.assertRaises(CidCritical) as context:
            render_from_template("","")
        self.assertTrue('mako.template.Template.render() argument after ** must be a mapping, not str' in str(context.exception))

if __name__ == '__main__':
    unittest.main()