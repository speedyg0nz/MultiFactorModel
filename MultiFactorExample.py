

# -*- coding: utf-8 -*-
"""
Created on Thu Mar 23 10:51:42 2016

@author: chongwee
"""

import MultiFactorModel as mfm

symbolsFilename     = 'symbols-shortlist.csv' #contains all the symbols to be considered
outputFilename      = 'analysisResult.csv' #filepath for the analysis outputs, leave empty to not write to file
startDate           = '2011-01-03' #start date to retrieve historical prices
endDate             = '2016-03-03' #end date to retrieve historical prices
analysisStartDate   = '2011-01-03' #usually same as price dates but this allows for additional flexibility in analysis, esp if certain stocks started trading later than others (e.g. FB, PYPL)
analysisEndDate     = '2016-02-03' #usually same as price dates but this allows for additional flexibility in analysis, esp if certain stocks started trading later than others (e.g. FB, PYPL)
analysisPeriod      = "monthly" #daily, weekly, monthly or yearly
benchmarkSymbol     = '^DJI' #benchmark stock/index to calculate excess returns against


try:
    mfm.performAnalysis(symbolsFilename,
                        startDate,
                        endDate,
                        analysisStartDate,
                        analysisEndDate,
                        analysisPeriod,
                        benchmarkSymbol,
                        outputFilename)

        
except ValueError as err:
    print(err.args[0])