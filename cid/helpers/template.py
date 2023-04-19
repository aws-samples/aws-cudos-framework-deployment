from mako import exceptions
from mako.template import Template

from cid.exceptions import CidCritical

def render_from_template(template_name, params = {}):
    try:
        tpl = Template(template_name, strict_undefined=True).render(**params)
        return tpl
    except:
        raise CidCritical(exceptions.text_error_template().render())