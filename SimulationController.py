# import sys
# from matplotlib.ticker import FuncFormatter
# import matplotlib.pyplot as plt


from SolarAssets import *
from SolarSimulation import *

import ReverseGeocode 

import datetime






# def FinancialFormatter(x, pos):
#     '''Converts a money amount into millions or billions if the value is big enough'''
    
#     # If under a million, print like normal
#     if x < 1e6:
#     	format = '$%1.1f' % x
#     # Else if under a billion print the amount in millions
#     elif x < 1e9:
#     	format = '$%1.1fM' % (x*1e-6)
#     # Else print as billions
#     else:
#     	format = '$%1.1fB' % (x*1e-9)

#     return format

# formatter = FuncFormatter(FinancialFormatter)

# # Output day simulation data to csv

# # f = open('averagePower.csv', 'w')
# # for day in powerResults['averagePower']:
# # 	f.write(str(day) + '\n')
# # f.close()

# # f = open('days.csv', 'w')
# # for day in powerResults['days']:
# # 	f.write(str(day) + '\n')
# # f.close()

# plt.figure(1)
# plt.subplot(311)
# plt.plot(powerResults['days'], powerResults['averagePower'])
# plt.title('Average Power of the PV farm')
# plt.ylabel('Power (kW)')

# plt.subplot(312)
# plt.plot(powerResults['days'], powerResults['sunnyTime'], 'g')
# plt.title('Electrical energy of the PV farm at GEP')
# plt.ylabel('Energy (kWh)')

# plt.subplot(313)
# plt.plot(powerResults['days'], powerResults['totalEffciency'], 'r')
# plt.title('Total efficiency of the PV farm')
# plt.ylabel('Efficiency (%)')

# # plt.figure(2)
# # a = plt.subplot(311)
# # a.yaxis.set_major_formatter(formatter)
# # plt.plot(financialResults['days'], financialResults['netAssetValue'])
# # plt.title('Net Asset Value')

# # a = plt.subplot(312)
# # a.yaxis.set_major_formatter(formatter)
# # plt.plot(financialResults['days'], financialResults['loanValue'], 'r')
# # plt.title('Loan Value')

# # a = plt.subplot(313)
# # a.yaxis.set_major_formatter(formatter)
# # plt.plot(financialResults['days'], financialResults['accumulativeRevenue'], 'g')
# # plt.title('Accumlative Revenue')

# plt.show()