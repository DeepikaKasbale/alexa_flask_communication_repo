# Carefully replace respective URLs according to your application. Below written URLs are just example of related URL which can't be used to run application.

# Write here suiteCRM instance's public IP you got from AWS EC2 along with suitecrm's folder name
# e.g: "http://18.111.12.92/suitecrm"
# Here Public IP is 'http://18.111.12.92' and  'suitecrm' is folder name located in 'var/www/'
SUITE_CRM_INSTANCE_IP_URL =  "http://18.111.12.92/suitecrm"

# Write here suiteCRM instance's http secured URL which is pointing to above public IP i.e http://18.111.12.92/suitecrm
# e.g: "https://suitcrm.demoexample.in"
SUITE_CRM_INSTANCE_BASE_URL = "https://suitcrm.demoexample.in"


SUITE_CRM_INSTANCE_REST_URL = SUITE_CRM_INSTANCE_BASE_URL + "/service/v4_1/rest.php"
SUITE_CRM_INSTANCE_OAUTH_URL = SUITE_CRM_INSTANCE_BASE_URL + "/api/oauth/access_token"
