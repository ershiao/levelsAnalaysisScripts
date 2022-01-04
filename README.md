
# Levels Analysis Scripts  <!-- omit in toc --> 

## Table of Contents <!-- omit in toc --> 
- [Overview](#overview)
- [Environment Setup](#environment-setup)
- [Scripts](#scripts)
  - [`analyze.py`](#analyzepy)
## Overview

The project focuses on providing a set of scripts to better sift through the self-provided salary data on levels.fyi[1].

[1] As far as I could tell, there isn't a publicized endpoint for the salary data but it seems like they push to a JSON dump periodically: https://www.levels.fyi/js/salaryData.json

## Environment Setup

This repo is primarily being developed with the use of Python 3 and pandas.

You may opt to set up your Python environment in whatever way fits you but I bootstrapped using Conda using the [pandas installation guide](https://pandas.pydata.org/getting_started.html) and everything seemed pretty quick and straightforward this way.


## Scripts

### `analyze.py`
`analyze.py` is a pulls down the JSON dump from levels.fyi[1] and then accepts title, stateCountry abbr., minimum salary, and years of experience as parameters. The results then get exported to a csv using the parameters as part of the file name. The intended use for the CSV is to put into some excel-like software for easy reading and basic manipulation.

In order to run, run `python analyze.py` from the directory and fill out the prompted inputs

[1] As of Jan. 3 2022, the script will locally cache the JSON dump to the script directory with an update period of 30 days since the file was last modified.