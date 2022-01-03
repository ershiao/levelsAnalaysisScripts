import pandas as pd
from pandas.core.frame import DataFrame
import requests
import numpy as np
import os
import json
import time
import datetime
import shutil

previousLevelsSalariesDir = 'previousLevelsSalaries'
levelsSalariesFilePath = 'levelsSalaries.json'
# 1 month in seconds
fileCacheUpdatePeriod = 30 * 24 * 60 * 60


def getSalaryDataDump():
    if (os.path.exists(levelsSalariesFilePath)
            and time.time() - os.path.getmtime(levelsSalariesFilePath) < fileCacheUpdatePeriod):
        print('Reading salaries from file')
        salariesFile = open(levelsSalariesFilePath)
        salaries = json.load(salariesFile)
        salariesFile.close()
    else:
        if (os.path.exists(levelsSalariesFilePath)
            and time.time() - os.path.getmtime(levelsSalariesFilePath) >= fileCacheUpdatePeriod):
            dateString = datetime.datetime.today().strftime('%Y-%m-%d')
            if (not os.path.exists(previousLevelsSalariesDir)) :
                os.mkdir(previousLevelsSalariesDir)
            shutil.move(levelsSalariesFilePath, f'{previousLevelsSalariesDir}/{dateString}.json')

        print('Salaries file not present or out of date. Fetching from `levels.fyi`.')
        salaries = requests.get(
            'https://www.levels.fyi/js/salaryData.json').json()
        newSalariesFile = open(levelsSalariesFilePath, 'w')
        json.dump(salaries, newSalariesFile)
    return salaries


def fixSalaryDF(df: DataFrame):
    # Filter out salary data older than a year
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    lookbackDatetime = datetime.datetime.now() - datetime.timedelta(days=365)
    fixedSalaryDf = df[df['timestamp']
                       > lookbackDatetime]

    fieldsToDrop = [
        'cityid',
        'dmaid',
        'rowNumber',
        'tag',
        'basesalary',
        'stockgrantvalue',
        'bonus',
        'gender',
        'otherdetails',
        'timestamp'
    ]
    fixedSalaryDf = (df
                     .drop(fieldsToDrop, axis=1)
                     .replace("", np.nan))

    numericFields = [
        'yearsofexperience',
        'totalyearlycompensation',
        'yearsatcompany'
    ]
    fixedSalaryDf[numericFields] = fixedSalaryDf[numericFields].apply(
        pd.to_numeric)

    return fixedSalaryDf


def filterSalaryDF(df: DataFrame, title: str, state: str, maxYearsOfExperience: int):
    filteredSalariesDf = df[df['title'] == title]
    filteredSalariesDf = filteredSalariesDf[filteredSalariesDf['location'].str.contains(
        f', {state}')]
    if(maxYearsOfExperience):
        filteredSalariesDf = filteredSalariesDf[filteredSalariesDf['yearsofexperience']
                                                <= maxYearsOfExperience + 2]

    return filteredSalariesDf


# TODO: Generalize the bounds
# TODO: Display counts + std. dev
def getPositionsWithSalaryRange(df: DataFrame, min: int):
    prunedSalaries = (df[df['totalyearlycompensation']
      .between(df['totalyearlycompensation'].quantile(.05),df['totalyearlycompensation'].quantile(.95))]
      )
    positionAvgSalariesDf = df.groupby(['company', 'level']).mean()

    print('275-350')
    print(positionAvgSalariesDf[(positionAvgSalariesDf['totalyearlycompensation']
          >= 275) & (positionAvgSalariesDf['totalyearlycompensation'] <= 350)])
    print('350-400')
    print(positionAvgSalariesDf[(positionAvgSalariesDf['totalyearlycompensation']
          >= 350) & (positionAvgSalariesDf['totalyearlycompensation'] <= 400)])
    print('400+')
    print(positionAvgSalariesDf[(positionAvgSalariesDf['totalyearlycompensation']
          >= 400)])

    return positionAvgSalariesDf[positionAvgSalariesDf['totalyearlycompensation'] > min]


def getTargetTitle(df: DataFrame):
    # TODO: Input validity check
    titles = df.groupby('title').size()
    print(titles)
    targetTitle = input('Enter title: ').strip()
    return targetTitle


def getTargetState(df: DataFrame):
    # TODO: Group by state or country instead of just location
    # TODO: Input validity check
    locations = df.groupby('location').size()
    print(locations)
    targetState = input('Enter state abbrevation: ').strip()
    return targetState


def getYearsOfExperience():
    # TODO: try/catch on double input
    return int(input('Enter years of experience: ').strip())


def exportDf(df: DataFrame):
    eligiblePositionsFilePath = 'eligiblePositions.csv'
    df.to_csv(eligiblePositionsFilePath)


def main():
    print('Getting salary data from levels and importing into dataframe')
    salariesDF = pd.DataFrame(getSalaryDataDump())
    print('Fixing salary dataframe')
    salariesDF = fixSalaryDF(salariesDF)

    targetTitle = getTargetTitle(salariesDF)
    targetState = getTargetState(salariesDF)
    yearsOfExperience = getYearsOfExperience()
    minSal = int(input('Enter target min salary: ;').strip())

    targettedSalariesDf = filterSalaryDF(
        salariesDF, targetTitle, targetState, yearsOfExperience)
    minSalariesDf = getPositionsWithSalaryRange(targettedSalariesDf, 275)

    print('Exporting results to `eligiblePositions.csv`')
    exportDf(minSalariesDf)


main()
