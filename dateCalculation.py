from datetime import *

class GMT(datetime):
    '''docstring for GMT'''
    def __init__(self, start=date.today(), finish):
        ''' The start and finish variables are tuples containing the year, month and day (in that order) '''
        self.start = date(start[0], start[1], start[2])
        self.finish = date(finish[0], finish[1], finish[2])
        self.days = start - finish
        self.dates = [self.start - datetime.timedelta(days=self.days) for self.days in range(0,numdays)]

    def getStartDate(self):
        return self.start

    def setStartDate(self, date):
        self.start = date

    def getFinishDate(self):
        return self.finish

    def setFinishDate(self, date):
        self.finish = date

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