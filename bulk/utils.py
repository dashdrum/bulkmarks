

from annoying.functions import get_object_or_None

from .models import ConfigSetting

#-----------------------------------------------------------------------------#

def get_config_setting(config_code):

	cs = get_object_or_None(ConfigSetting, config_code=config_code)

	if cs:
		return cs.config_value

	return None

