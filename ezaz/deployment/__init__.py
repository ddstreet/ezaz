
import json
import jsonschema

from abc import ABC
from abc import abstractmethod
from collections import UserDict


class DeploymentTemplate(UserDict, ABC):
    DEFAULT_SCHEMA = 'https://schema.management.azure.com/schemas/2015-01-01/deploymentTemplate.json#'
    DEFAULT_CONTENT_VERSION = '1.0.0.0'

    def __init__(self, *, schema=None, content_version=None, **parameters):
        super().__init__()
        self['$schema'] = schema or self.DEFAULT_SCHEMA
        self['contentVersion'] = content_version or self.DEFAULT_CONTENT_VERSION

    @property
    @abstractmethod
    def schema(self):
        pass

    def to_json(self, indent=None):
        return json.dumps(self.to_dict(), indent=indent)

    def to_dict(self):
        return dict(self)

    def validate(self):
        if not self.schema:
            return

        try:
            jsonschema.validate(self.to_dict(), schema=self.schema)
        except jsonschema.ValidationError as ve:
            raise RuntimeError(f'Validation failed: {ve}') from ve
