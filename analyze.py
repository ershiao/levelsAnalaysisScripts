# analyze.py is a script meant to be run in CLI that pulls down* the JSON dump
# from levels.fyi and then accepts title, stateCountry abbr., minimum salary, and
# years of experience as parameters. The results then get exported to a csv using
# the parameters as part of the file name. The intended use for the CSV is to put into
# some excel-like software for easy reading and basic manipulation.

# * The script attempts to locally cache the JSON dump into the same folder
# with an update period of 30 days
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
# 30 days in seconds
fileCacheUpdatePeriod = 30 * 24 * 60 * 60


def getSalaryDataDump():
    if (os.path.exists(levelsSalariesFilePath)
            and time.time() - os.path.getmtime(levelsSalariesFilePath) < fileCacheUpdatePeriod):
        print('Reading salaries from file')
        salariesFile = open(levelsSalariesFilePath)
        salaries = json.load(salariesFile)
        salariesFile.close()
    else:
        # Cache previous dump file
        if (os.path.exists(levelsSalariesFilePath)
                and time.time() - os.path.getmtime(levelsSalariesFilePath) >= fileCacheUpdatePeriod):
            dateString = datetime.datetime.today().strftime('%Y-%m-%d')
            if (not os.path.exists(previousLevelsSalariesDir)):
                os.mkdir(previousLevelsSalariesDir)
            shutil.move(levelsSalariesFilePath,
                        f'{previousLevelsSalariesDir}/{dateString}.json')

        print('Salaries file not present or out of date. Fetching from `levels.fyi`.')
        salaries = requests.get(
            'https://www.levels.fyi/js/salaryData.json').json()
        newSalariesFile = open(levelsSalariesFilePath, 'w')
        json.dump(salaries, newSalariesFile)
    return salaries

# TODO: Cache data fixing results, runtime mostly spent on this right now.


def fixSalaryDF(df: DataFrame):
    # Filter out salary data older than a year
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    lookbackDatetime = datetime.datetime.now() - datetime.timedelta(days=365 * 2)
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

    return fixedSalaryDf.reset_index()


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
    prunedSalaries = (df[
        df['totalyearlycompensation']
        .between(df['totalyearlycompensation'].quantile(.05), df['totalyearlycompensation'].quantile(.95))
    ])
    counts = prunedSalaries.groupby(
        ['company', 'level']).size().to_frame('count')

    positionAvgSalariesDf = (prunedSalaries.groupby(['company', 'level']).agg(
        tcMean=(
            'totalyearlycompensation', 'mean'),
        tcStd=(
            'totalyearlycompensation', 'std'),
        yoeMean=(
            'yearsofexperience', 'mean'),
        yoeStd=(
            'yearsofexperience', 'std'),
        yearsatcompany=('yearsatcompany', 'mean')
    )
    )

    positionAvgSalariesDf = pd.merge(
        positionAvgSalariesDf, counts, on=['company', 'level'])
    return positionAvgSalariesDf[positionAvgSalariesDf['tcMean'] > min]


def getTargetTitle(df: DataFrame):
    # TODO: Input validity check
    titles = df.groupby('title').size()
    print(titles)
    targetTitle = input('Enter title: ').strip()
    return targetTitle


def getTargetState(df: DataFrame):
    # TODO: Group by state or country instead of just location
    # TODO: Input validity check
    countryState = df['location'].str.extract(
        r'(?<=, )(\w\w)(?=,)?',
        expand=False
    )
    locations = df.groupby(countryState).size()
    print(locations)
    targetState = input('Enter country/state abbrevation: ').strip()
    return targetState


def getYearsOfExperience():
    # TODO: try/catch on double input
    return int(input('Enter years of experience: ').strip())


def exportDf(df: DataFrame, title: str, countryState: str, yoe: int, minSalary: int):
    dateString = datetime.datetime.today().strftime('%Y-%m-%d')
    eligiblePositionsFilePath = f'eligiblePositions/{title}_{countryState}_{yoe}yoe_{minSalary}salary_{dateString}.csv'
    print(f'Exporting results to `{eligiblePositionsFilePath}`')
    df.to_csv(eligiblePositionsFilePath)


def main():
    print('Getting salary data from levels and importing into dataframe')
    salariesDF = pd.DataFrame(getSalaryDataDump())
    print('Fixing salary dataframe')
    salariesDF = fixSalaryDF(salariesDF)

    targetTitle = getTargetTitle(salariesDF)
    targetState = getTargetState(salariesDF)
    yearsOfExperience = getYearsOfExperience()
    minSalary = int(input('Enter target min salary (in thousands): ').strip())

    targettedSalariesDf = filterSalaryDF(
        salariesDF, targetTitle, targetState, yearsOfExperience)
    minSalariesDf = getPositionsWithSalaryRange(
        targettedSalariesDf, minSalary)
    exportDf(minSalariesDf, targetTitle, targetState,
             yearsOfExperience, minSalary)


main()
