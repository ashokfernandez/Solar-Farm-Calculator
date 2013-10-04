def dateToIndex(date):
	''' Returns the index of the day and the month of the datetime object given.
	The returned value is a tuple in the form (day, month) where the day is an integer
	between 0 and 364 and month is an integer 0 - 11 so they can be used an an array index'''
	# Get the date of the first day of the year
	startOfYear = datetime.date(date.year, 1, 1)
	
	# Calculate the day of the year as a value between 0 and 364
	dayOfYear = date - startOfYear
	dayOfYear = dayOfYear.days
	
	# Get the month of the year as an array index
	month = date.month - 1

	return (dayOfYear, month)

