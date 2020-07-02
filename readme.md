# Linkedin Spider

## Description

This demo shows a simple Linkedin Spider for scraping profiles given some basic information.

## Functionality

1. login to the Linkedin according to given username and password
2. extract Linkedin profile urls in Google search engine
3. jump to the first result of Google search, extract more info about the target
4. write results back to a xls file

To avoid Google captcha validation, for sure Linkedin login validation, 
we suggest to enter the validation code and do the "I'm not a robot" test manually for the 
first time, then leave the work to the program. This program waits a few seconds after every
profile extraction and restarts the spider for every several profiles are parsed to avoid 
memory leakage.  
