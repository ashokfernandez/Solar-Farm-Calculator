import ReverseGeocode
import Countries
import json
import AverageTemperatureData

code = ReverseGeocode.get_country_code(31.653381,-6.108398)

if code != False:
	print Countries.LONG_CODE_TO_NAME[code]
	print AverageTemperatureData.TEMPERATURE_DATA[code]['FUTURE']
else:
	print "Google couldn't locate a supported country at that location"