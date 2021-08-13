import yaml

from helpers.concepts import OpenShiftTemplate


class TestOpenShiftTemplate:
    def test_render_template_env_vars(self):
        """Separate ENV vars in the deployment"""
        template = OpenShiftTemplate("test")
        env_vars = ["key1", "key2"]
        template_yaml = yaml.safe_load(template.render_template(env_vars=env_vars))
        deployment = template_yaml["objects"][1]
        assert deployment["spec"]["template"]["spec"]["containers"][0]["env"] == [
            {"name": "key1", "value": "some_value"},
            {"name": "key2", "value": "some_value"},
        ]

    def test_render_template_config_map(self):
        """Separate config map that is referenced from by the deployment"""
        template = OpenShiftTemplate("test")
        cm_keys = ["key1", "key2"]
        template_yaml = yaml.safe_load(template.render_template(cm_keys=cm_keys))
        config_map = template_yaml["objects"][2]
        assert config_map["kind"] == "ConfigMap"
        assert config_map["data"] == {"key1": "some_value", "key2": "some_value"}
        # Check if there is a ref to the config map in the deployment
        deployment = template_yaml["objects"][1]
        assert deployment["spec"]["template"]["spec"]["containers"][0]["envFrom"] == [
            {"configMapRef": {"name": "test-${env}"}}
        ]

    def test_render_template_secrets(self):
        """Separate secrets that is referenced from by the deployment"""
        template = OpenShiftTemplate("test")
        secrets = ["key1", "key2"]
        template_yaml = yaml.safe_load(template.render_template(secrets=secrets))
        secret = template_yaml["objects"][2]
        assert secret["kind"] == "Secret"
        assert secret["stringData"] == {"key1": "", "key2": ""}
        # Check if there is a ref to the secret in the deployment
        deployment = template_yaml["objects"][1]
        assert deployment["spec"]["template"]["spec"]["containers"][0]["envFrom"] == [
            {"secretRef": {"name": "test-${env}"}}
        ]
