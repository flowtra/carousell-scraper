# Carousell Scraper

## Problem

As part of a small side hustle flipping iPhones (buying low, selling higher), I had to laboriously & manually scroll through individual Carousell listings to find eligible iPhones listed for cheap. I then had to gather details such as storage capacity, battery health etc. and key it into another phone buyback website to get the shops buyback prices.

## Solution

I created two solutions for this project.
1. An automatic scraper that can retrieve the details of hundreds of listings in seconds - allowing me to then filter out potential “good deals” via further data processing in Google Sheets/Excel.
2. An automatic buyback-price checker - while following up on these potential listings in a selenium browser, i’d press a key in the python console which let the program retrieve the listing’s details, and submit it to the buyback-price website’s API, which I also reverse engineered to use. It would then print out the buyback price from the API response.

