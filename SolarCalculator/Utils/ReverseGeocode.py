import Countries				  # Contains all the countrie codes and names
import urllib2                    # For downloading the currency data
import json                       # Allows the data to be decoded

BASE_URL = "http://maps.googleapis.com/maps/api/geocode/json?latlng=%f,%f&sensor=false"

class CountryNotFound(Exception):
	''' Raised when the geocode could not find a country'''
	pass

# --------------------------------------------------------------------------------------------------------------------
# MISC FUNCTIONS
# --------------------------------------------------------------------------------------------------------------------

DEBUG_MODE = True

def debug(message):
    ''' Prints debugging messages if debug mode is set to true'''
    if DEBUG_MODE:
        print message

def find_short_country_code(result):
	''' Takes a result from the Google reverse GeoCoding API and finds a short country code'''
	
	# Search through the result component
	for component in result['address_components']:
		
		# If they type of result is a country save the short ALPHA-2 name
		if 'country' in component['types']:
			shortCountryCode = component['short_name']
			break

		# Otherwise mark that is wasn't found
		else:
			shortCountryCode = False

	return shortCountryCode


def get_country_code(lat, lng):
	''' Takes a Latitude and Longtitude value and uses Google Maps to reverse Geocode it 
	into a three letter ISO ALPHA-3 country code if possible. Returns false if the Geocoding
	failed or if the country found wasn't supported. '''

	# Generate the URL for a reverse GeoCode search to Google Maps
	GMAPS_URL = BASE_URL % (lat, lng)

	try:
		# Query Google Maps with the Latitude and Longtitude
		gmapsResult = urllib2.urlopen(GMAPS_URL)
		gmapsResultJSON = gmapsResult.read()
		gmapsResultDecoded = json.loads(gmapsResultJSON)

	except:
		debug("Failed to get location from google maps")
		return False

	# Check result was OK
	if gmapsResultDecoded['status'] == "OK":
		shortCountryCode = False		
		
		# Traverse through the dictionary to find a short country code
		for result in gmapsResultDecoded['results']:
			shortCountryCode = find_short_country_code(result)
			
			# If one was found, stop looking
			if shortCountryCode != False:
				break
		
		# Convert to the standard three letter ALPHA-3 country code used by the rest of the program
		longCountryCode = Countries.SHORT_CODE_TO_LONG_CODE[shortCountryCode]

		return longCountryCode
	
	else:
		debug("Google lookup failed for lat,lng: %f,%f" % (lat,lng))
		return False





