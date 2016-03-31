# -*- coding: utf-8 -*-
"""
Created on Thu Mar 23 10:51:42 2016

@author: chongwee
"""
import csv
from yahoo_finance import Share
import os
from sys import exit
import datetime as dt
import calendar
import requests
import matplotlib.pyplot as plt
import statsmodels.formula.api as sm
import statsmodels.api as sma
import pandas as pd
from sklearn.metrics import mean_squared_error

def readSymbolsCSV(filepath):
    symbols = []    
    with open(filepath, 'r', newline='\n', encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:            
            symbols.append(row[0])
    f.close()
    return symbols
    
def readDatesCSV(filepath):
    dates = []    
    with open(filepath, 'r', newline='\n', encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:            
            dates.append(row[0])
    f.close()
    return dates 

def findLastTradingDayInPeriods(start,end,allTradingDates,frequency):
            
    startDate = dt.datetime.strptime(start, '%Y-%m-%d')
    endDate = dt.datetime.strptime(end, '%Y-%m-%d')

    lastTradingDays = []
    date = startDate        
    
    allDatesInPeriod = []
    while date <= endDate: 
        allDatesInPeriod.append(date.strftime('%Y-%m-%d'))
        if meetsDateRequirements(date,frequency):
            tradingDaysInPeriod = list(set(allTradingDates).intersection(allDatesInPeriod))
            if len(tradingDaysInPeriod) > 0:             
                lastTradingDays.append(max(tradingDaysInPeriod)) #append last/max trading day in period
            allDatesInPeriod = []
        date += dt.timedelta(days=1)     
    
    return lastTradingDays        

def meetsDateRequirements(date,frequency):
    if frequency == "daily":    
        return True
    elif frequency == "weekly":
        if date.isoweekday() == 7:
            return True
        else:
            return False
    elif frequency == "monthly":
        lastDayInMonth = calendar.monthrange(date.year,date.month)[1]
        if date.day == lastDayInMonth:
            return True
        else:
            return False
    elif frequency == "yearly":
        if date.day == 31 and date.month == 12:
            return True
        else:
            return False   
    else:
        print("Invalid frequency parameter passes to meetsDateRequirements")
        exit(0); #exit program due to invalid input (neither daily, weekly, monthly or yearly)

def retrieveQuoteFromGoogle(symbol,start_date,end_date):
    start = dt.date(int(start_date[0:4]),int(start_date[5:7]),int(start_date[8:10]))
    end = dt.date(int(end_date[0:4]),int(end_date[5:7]),int(end_date[8:10]))
    url_string = "http://www.google.com/finance/historical?q={0}".format(symbol)
    url_string += "&startdate={0}&enddate={1}&output=csv".format(start.strftime('%b %d, %Y'),end.strftime('%b %d, %Y'))    
    response = requests.get(url_string)
    quoteDict = {}  
    if response.status_code == 200:        
        open('temp.csv', 'wb').write(response.content)    
        with open('temp.csv', 'r', newline='\n', encoding="utf-8") as f:
            reader = csv.reader(f)
            reader.next()            
            for row in reader:            
                date = dt.datetime.strptime(row[0], '%d-%b-%y')
                dateStr = date.strftime('%Y-%m-%d')
                quoteDict[dateStr] = float(row[4])  
        f.close()  
    else:
        raise Exception('Unable to find quote on Google Finance')          
    print(quoteDict)
    return quoteDict #return close price from last trading day of week since it might not be friday     

def retrieveQuoteFromYahoo(symbol,start,end):        
    share = Share(symbol)  
    quoteList = share.get_historical(start,end)
    quoteDict = {}
    for quote in quoteList:
        quoteDict[quote['Date']] = float(quote['Adj_Close'])        
    return quoteDict

def retrieveHistoricalQuotes(symbol,start,end):    
    print("Retrieving historical prices for {0}...".format(symbol))    
    
    if checkFileExists(symbol,start,end):
        return readQuotesFromCSV(symbol,start,end)
    else:
        quoteDict = {}
        try:
            quoteDict = retrieveQuoteFromGoogle(symbol,start,end)
        except:
            quoteDict = retrieveQuoteFromYahoo(symbol,start,end)
        writeQuotesToCSV(symbol,start,end,quoteDict)
        return quoteDict

def readQuotesFromCSV(symbol,start,end):
    quotes = {}    
    directory = "quotes"
    filename = "{0}_{1}_{2}.csv".format(symbol,start,end)
    with open(os.path.join(directory,filename), 'r', newline='\n', encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:            
            quotes[row[0]] = float(row[1])
    f.close()
    return quotes

def writeQuotesToCSV(symbol,start,end,quotes):
    directory = "quotes"
    if not os.path.exists(directory):
        os.makedirs(directory)
    filename = "{0}_{1}_{2}.csv".format(symbol,start,end)
    with open(os.path.join(directory,filename), 'w', newline="\n", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        dates = quotes.keys()        
        for date in sorted(dates):        
            cells = [date,quotes[date]]                    
            writer.writerow(cells)        
    csvfile.close()
 


def checkFileExists(symbol,start,end):
    directory = "quotes"
    filename = "{0}_{1}_{2}.csv".format(symbol,start,end)
    if not os.path.exists(os.path.join(directory,filename)):
        return False
    else:
        return True    

def readNameSectorCSV(filepath):
    stockDictionary = {}    
    with open(filepath, 'r', newline='\n', encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:     
            nameSectorDictionary = {}
            nameSectorDictionary['Name'] = row[1]
            nameSectorDictionary['Sector'] = row[2]
            stockDictionary[row[0]] = nameSectorDictionary
    f.close()
    return stockDictionary

def retrieveSectorSymbol(sectorName):      
    switcher = {
        "Consumer Discretionary" : "XLY",
        "Consumer Staples": "XLP",
        "Energy": "XLE",
        "Financial Services": "XLFS",
        "Financials": "XLF",
        "Health Care": "XLV",
        "Industrials": "XLI",
        "Materials": "XLB",
        "Real Estate": "XLRE",
        "Information Technology": "XLK", #both info tech and telecomms point to XLK
        "Telecommunications Services": "XLK", #both info tech and telecomms point to XLK
        "Utilities": "XLU"        
    }
    return switcher[sectorName]


def writeToFile(filename, text):    
    outputFile = open(filename, "w", encoding="utf-8")
    outputFile.write(text)
    outputFile.close()

def performAnalysis(symbolsFilename,startDate,endDate,analysisStartDate,analysisEndDate,analysisPeriod,benchmarkSymbol,outputFilename):
    quotes = retrieveHistoricalQuotes("^DJI",startDate,endDate)
    allTradingDays = sorted(quotes.keys())
    dates = findLastTradingDayInPeriods(analysisStartDate,analysisEndDate,allTradingDays,analysisPeriod)
    names_sectors = readNameSectorCSV('sectors.csv')
    
    benchmarkQuotes = retrieveHistoricalQuotes(benchmarkSymbol,startDate,endDate)
    sectorQuotes = {}
    sectors = ['XLY','XLP','XLE','XLF','XLV','XLI','XLB','XLK','XLU']    
    for sector in sectors:    
        sectorQuotes[sector] = retrieveHistoricalQuotes(sector,startDate,endDate)
        
    #start by getting the list of symbols to be considered for shortlisting
    symbols = sorted(readSymbolsCSV(symbolsFilename))
    
    #retrieve historical prices and calculate returns
    equitiesReturns = {}
    benchmarkReturns = []
    sectorReturns = {}
    df = pd.DataFrame({"Dates":dates[1:]})
    
    for symbol in symbols:
        quotes = retrieveHistoricalQuotes(symbol,startDate,endDate)
        sector = names_sectors[symbol]['Sector']        
        sectorSymbol = retrieveSectorSymbol(sector)
        stockReturns = []
        sectorReturn = []
             
        previousTime = dates[0]
        for currentTime in dates[1:]:
            try:
                prev = quotes[previousTime]
                curr = quotes[currentTime]
                stockReturn = (curr-prev)/prev
                stockReturns.append(stockReturn) #multiply by 100 if you work using percent

                benchmarkPrev = benchmarkQuotes[previousTime]
                benchmarkCurr = benchmarkQuotes[currentTime]
                benchmarkReturn = (benchmarkCurr-benchmarkPrev)/benchmarkPrev
                if len(equitiesReturns) == 0:                
                    benchmarkReturns.append(benchmarkReturn) #multiply by 100 if you work using percent
                                        
                sectorPrev = sectorQuotes[sectorSymbol][previousTime]
                sectorCurr = sectorQuotes[sectorSymbol][currentTime]
                sectorExcessReturn = (sectorCurr-sectorPrev)/sectorPrev
                sectorExcessReturn = sectorExcessReturn - benchmarkReturn
                sectorReturn.append(sectorExcessReturn) #multiply by 100 if you work using percent                    
                    
            except KeyError:       
                raise ValueError("Missing quotes for {0} between {1} and {2}".format(symbol,previousTime,currentTime))
            previousTime = currentTime
        equitiesReturns[symbol] = stockReturns
        sectorReturns[sectorSymbol] = sectorReturn        
        df[symbol] = stockReturns
        df[sectorSymbol] = sectorReturns[sectorSymbol]
    
    df["Benchmark"] = benchmarkReturns            
    print(df.head())
    
    analysisComponents = [1,2,3,4]
    
    if 1 in analysisComponents:
        
        print("\n\n========== Single Factor Model (Market) ==========\n\n")
        summaries = ""
        adjrsquaredValues = {}
        for symbol in symbols:
            
            name = names_sectors[symbol]['Name']
            
            print("\n===== Regression Results ({} / {}) =====\n".format(name,"DJI"))                
                  
            result = sm.ols(formula='{} ~ Benchmark'.format(symbol), data=df).fit()
            print("Adj R-squared:\t{}".format(result.rsquared_adj))
            print("Coefficient:\n{}".format(result.params))
            print("P-Value:\n{}".format(result.pvalues))
                    
            summaries += (name + "\n\n" + result.summary().as_text() + "\n\n")
    
            plt.plot(df["Benchmark"], df[symbol], 'ro')
            plt.plot(df["Benchmark"], result.fittedvalues, 'b')        
            plt.ylim(-0.4, 0.4)
            
            plt.legend(['Data', 'Fitted model'])
            plt.xlabel("Benchmark Returns (DJI)")
            plt.ylabel("Stock Returns ({})".format(symbol))
            plt.title("Linear Regression ({} / DJI)".format(name))        
            plt.savefig("{}.png".format(symbol))        
            plt.show()   
                        
            adjrsquaredValues[symbol] = result.rsquared_adj
            
        keys = sorted(adjrsquaredValues.keys())
        for symbol in keys:         
            name = names_sectors[symbol]['Name']
            print("{}|{}|{}".format(symbol,name,adjrsquaredValues[symbol]))
        
        writeToFile("lm.txt",summaries)
        
    if 2 in analysisComponents:        
                
        print("\n\n========== Two Factor Model (Market, Sector) - 5 years ==========\n\n")
        adjrsquaredValues = {}
        summaries = ""

        for symbol in symbols:
            
            sector = names_sectors[symbol]['Sector']        
            sectorSymbol = retrieveSectorSymbol(sector)
            name = names_sectors[symbol]['Name']
            
            print("\n===== Regression Results ({} / {}) =====\n".format(name,sector))                
                  
            result = sm.ols(formula='{} ~ Benchmark + {}'.format(symbol,sectorSymbol), data=df).fit()
            print("Adj R-squared:\t{}".format(result.rsquared_adj))
            print("Coefficients:\n{}".format(result.params))
            print("P-Values:\n{}".format(result.pvalues))
    
            summaries += (name + "\n\n" + result.summary().as_text() + "\n\n")
    
            adjrsquaredValues[symbol] = result.rsquared_adj
            

        keys = sorted(adjrsquaredValues.keys())
        for symbol in keys:        
            name = names_sectors[symbol]['Name']
            sector = names_sectors[symbol]['Sector']   
            print("{}|{}|{}|{}".format(symbol,name,sector,adjrsquaredValues[symbol]))

        writeToFile("lm2.txt",summaries)

    
    if 3 in analysisComponents:        

        print("\n\n========== Two Factor Model (Market, Sector) - Out-of-Sample Predictions ==========\n\n")
        
        mseValues = {}
        for symbol in symbols:
            
            sector = names_sectors[symbol]['Sector']        
            sectorSymbol = retrieveSectorSymbol(sector)
            name = names_sectors[symbol]['Name']
            
            print("\n===== Regression Results ({} / {}) =====\n".format(name,sector))                
            
            predictions = []
            actual = []
            for i in range(48,60):
                result = sm.ols(formula='{} ~ Benchmark + {}'.format(symbol,sectorSymbol), data=df.head(i)).fit()        
                testdf = df[['Benchmark',sectorSymbol]]
                prediction = result.predict(testdf[i:i+1]) 
                predictions.append(prediction[0])
                actual.append(df.iloc[i][symbol])
            
            print("Actual values:\t{}".format(actual))
            print("Predicted values:\t{}".format(predictions))
            print("MSE Out-of-sample:\t{}".format(mean_squared_error(actual, predictions)))
            
            mseValues[symbol] = mean_squared_error(actual, predictions)

        keys = sorted(mseValues.keys())
        for symbol in keys:                
            name = names_sectors[symbol]['Name']
            sector = names_sectors[symbol]['Sector']   
            print("{}|{}|{}|{}".format(symbol,name,sector,mseValues[symbol]))

    if 4 in analysisComponents:        
   
        print("\n\n========== ARMA Model ==========\n\n")
        
        bicValues = {}
        for symbol in symbols:
            AR_lag = 1
            MA_lag = 1
            data = df[symbol].values
            model = sma.tsa.ARMA(data, (AR_lag, MA_lag)).fit(transparams=False)    
            print(model.summary())
            bicValues[symbol] = model.bic
        
        keys = sorted(bicValues.keys())
        for symbol in keys: 
            bic = bicValues[symbol]
            name = names_sectors[symbol]['Name']
            sector = names_sectors[symbol]['Sector']   
            print("{}|{}|{}|{}".format(symbol,name,sector,bic))     
        
        
    print("Analysis Complete.")