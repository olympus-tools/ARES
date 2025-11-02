from typing import override

from ares.utils.custom_plugins import AresPlugin


class ares_customplugin(AresPlugin):
    @override
    def execute(self):
        self.log.warning("Custom was executed!")
