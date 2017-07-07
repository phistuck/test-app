from google.appengine.ext.webapp import template

from constants import TEMPLATE_PATH, APPLICATION_TITLE, \
 COPYRIGHT_YEAR_RANGE, COPYRIGHT_HOLDER, \
 GOOGLE_SITE_VERIFICATION, VERIFY_V1

standard_values = \
 { \
  'application_title': APPLICATION_TITLE, \
  'copyright_year_range': COPYRIGHT_YEAR_RANGE, \
  'copyright_holder': COPYRIGHT_HOLDER, \
  'verify_v1': VERIFY_V1, \
  'google_site_verification': GOOGLE_SITE_VERIFICATION \
 }

def render_template(values):
 template_values = standard_values.copy()
 template_values.update(values)
 return unicode(template.render(TEMPLATE_PATH, template_values))