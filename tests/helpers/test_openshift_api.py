import os

import responses
import pytest
import yaml

from helpers.openshift_api import OpenShiftAPI


@pytest.fixture
def open_shift_api():
    return OpenShiftAPI("https://localhost", "token")


@responses.activate
def test_create_process_template(open_shift_api):
    template_url = (
        "https://localhost/apis/template.openshift.io/v1/namespaces/project/templates"
    )
    processed_template_url = "https://localhost/apis/template.openshift.io/v1/namespaces/project/processedtemplates"
    service_url = "https://localhost/api/v1/namespaces/project/services"
    deployments_url = "https://localhost/apis/apps/v1/namespaces/project/deployments"
    trigger_url = (
        "https://localhost/apis/apps/v1/namespaces/project/deployments/appname-tst"
    )
    config_map_url = "https://localhost/api/v1/namespaces/project/configmaps"

    secret_url = "https://localhost/api/v1/namespaces/project/secrets"

    template_path = os.path.join(os.getcwd(), "tests", "resources", "template.yml")
    with open(template_path, "r") as file:
        template_data = file.read()
        template_yaml_object: dict = yaml.safe_load(template_data)

    # processed_template = {"objects": ["service", "deployment", "configmap"]}

    responses.add(responses.POST, template_url)
    responses.add(responses.POST, processed_template_url, json=template_yaml_object)
    responses.add(responses.POST, service_url)
    responses.add(responses.POST, deployments_url)
    responses.add(responses.PATCH, trigger_url)
    responses.add(responses.POST, config_map_url)
    responses.add(responses.POST, secret_url)

    open_shift_api.create_process_template("project", "appname", ["tst"], template_data)

    assert len(responses.calls) == 7
