import logging
from typing import Any, Dict

from freqtrade.configuration import (Configuration, remove_credentials,
                                     validate_config_consistency)
from freqtrade.state import RunMode

logger = logging.getLogger(__name__)


def setup_utils_configuration(args: Dict[str, Any], method: RunMode) -> Dict[str, Any]:
    """
    Prepare the configuration for utils subcommands
    :param args: Cli args from Arguments()
    :return: Configuration
    """
    configuration = Configuration(args, method)
    config = configuration.get_config()

    # Ensure we do not use Exchange credentials
    remove_credentials(config)
    validate_config_consistency(config)

    return config
