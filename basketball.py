# -*- coding: utf-8 -*-
import pandas as pd

from urllib.request import urlopen
from bs4 import BeautifulSoup

# Just this variable needs to be changed to look at a different season.
year = 2020

'''
Using .format() fills in the `{}` in the URL with the year listed above.
Just makes it slightly easier to edit this script the next year as long as the 
URL format for this website stays the same.
'''
url = "https://www.basketball-reference.com/leagues/NBA_{}_per_game.html".format(year);

# urlopen is from the urllib package
html = urlopen(url);

# Use the webpage's HTML to make a BeautifulSoup object to scrape data easily.
soup = BeautifulSoup(html);

'''
Within each `tr` tag, there are many `th` tags for each column in that row.
The `th` tags within the first `tr` tag are the column headers for the stats.

The command below retrieves these column headers and sorts it into a list,
which will be used to format our DataFrame later.
'''
headers = []

'''
`scraped_headers` is a list of all of the headers from the first row of the 
data set found by using the tag `th`. However, each element in this list is
still in the raw HTML format with many other HTML components besides the single
word we want for the header title (ex: "PTS", "REB", etc).

`tr` is the tag used in the HTML for each row of data, including the header row.

[1:] is applied at the end because we do not care about the meaningless `Rank`
column at the very left of the data set. (Rank just counts up how many total
players there are, and this is done automatically anyways by row indexing in
a Pandas DataFrame.)

Again, 'th' is the tag used for each column element within each row ('tr').
'''
scraped_headers = soup.findAll('tr', limit = 1)[0].findAll('th')[1:];

for th in scraped_headers:
    headers.append(th.getText());

'''
The findAll() command used to find `rows` retrieves the content of ALL `tr`
tags in the HTML of the website except the first tag, which are the headers
that we extracted earlier (which is why [1:] is used.

'rows' is basically a list of the raw HTML contained within each 'tr' tag,
which contain each player's stats, which is why each element of this list
can be thought of as a row for the data table we are about to construct.
'''
rows = soup.findAll('tr')[1:];

# A 2-D list of all player data.
player_stats = [];

for i in range(len(rows)):
    # The current player's stats
    curr_player = [];
    
    # Add each stat column by column to the current player
    # 'td' is the tag used for the data in each column for the current player.
    for td in rows[i].findAll('td'):
        # The 'td' tags are in order of the column headers, so simply append.
        curr_player.append(td.getText());
    
    #Add the completed stat row to the 2-D array `player_stats`
    player_stats.append(curr_player);

# Use our 2-D list of stats and list of header names to construct a DataFrame.
stats = pd.DataFrame(player_stats);
stats.columns = headers;

'''
Remove sub-header rows from DataFrame (They have None and NaN as row values)
Sub-header rows were in the original web page to show which column is which
stat as you scrolled down. That is useless information for our purposes.
'''
for row in stats.index:
    if (stats.loc[row, 'Player'] is None):
        stats.drop(row, inplace=True);
        
stats.reset_index(drop=True, inplace=True);

'''
Some players have moved around teams within this season. Therefore, their name
appears multiple times in the DataFrame and takes up multiple rows. 

The code below collapses these rows into one row. The first row their name 
appears actually has their total stats. The last row with their name contains
the current team they play for. The team for the first row they appear in is
listed as 'TOT' (Signifiying Total stats), so the team name has to be swapped
with the team name that appears in the last row their name appears. Then,
all rows besides the first one their name appears in can be dropped.

The method used below assumes that no player in the NBA shares the same exact
name and age. If the NBA ever has two players with the same name and age, this
method will have to be modified.
'''

# First, map name+age to # of appearances using a dictionary.
names_freq = {};

# Load name+age keys into dictionary w/ their frequencies.
for row in stats.index:
    curr_player = stats.loc[row, 'Player'] + stats.loc[row, 'Age'];
    if curr_player in names_freq.keys():
        names_freq[curr_player] = names_freq.get(curr_player) + 1;
    else:
        names_freq[curr_player] = 1;
        
# Remove key-value pairs if the name+age only appeared once.
keys_to_remove = [];
for player in names_freq.keys():
    if (names_freq.get(player) == 1):
        keys_to_remove.append(player);
        
for key in keys_to_remove:
    names_freq.pop(key);
    
'''
Now, `names_freq` should only contain players that appear in more than one row
in the stats. Again, the first row they appear in has the proper, total stats
across all teams they have been on this season. The value in the key-value
pairs in `names_freq` will help navigate to the last row in which the player
appears to access their current team and change the value in the first row.

Then, all subsequent rows that the player appears in after the first, modified
row will be dropped. 

After these rows are dropped, that player's key-value pair in 'names_freq'
will be dropped to get closer to one of the exit conditions of the while loop
below, which is more efficient and avoids some indexing issues.
'''
row = 0;
while row < len(stats.index) and len(names_freq.keys()) > 0:
    curr_player = stats.loc[row, 'Player'] + stats.loc[row, 'Age'];
    if curr_player in names_freq.keys():
        correct_team_row = row + names_freq.get(curr_player);
        stats.at[row, 'Tm'] = stats.at[correct_team_row, 'Tm'];
        for i in range(1, names_freq.get(curr_player)):
            stats.drop(row + i, inplace=True);
        row += names_freq.get(curr_player);
        names_freq.pop(curr_player);
    else:
        row+=1;
        
stats.reset_index(drop=True, inplace=True);

# Convert all numbers from str to float from column 'Games Played' and onward.
# (The DataFrame stored these values as strings by default when scraping.)
   
'''
#Brute force, inelegant method. It works.
#converts to float, not numpy.float64
for column in stats.columns[4:]:
    for row in range(len(stats.index)):
        curr_cell = stats.loc[row, column];
        try:
            if(isinstance(curr_cell, str)):
                stats.at[row, column] = float(stats.loc[row, column]);
        except ValueError:
            stats.at[row,column] = 0.0;
'''
 
'''
#astype() method, does not pass type checks
print(type(stats.at[1,'MP']));

convert_dict = {};
for column in stats.columns[4:]:
    convert_dict[column] = float;
    
print(convert_dict)
stats.astype(convert_dict, errors = 'ignore');

print(type(stats.at[1,'MP']));
'''

# to_numeric method, passes type checks. (more elegant)
# converts to numpy.float64, not float.
# print(type(stats.at[1,'G'])); # - a type pre-check

for column in stats.columns[4:]:
    stats[column] = pd.to_numeric(stats[column]);

#print(type(stats.at[1,'G'])); # - a type post-check

# Make the data set and any output easier to see and read on the console.
pd.set_option('display.max_rows', 1000)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

print(stats);

# Simple query into the DataFrame to test that the data set is ready for use.
# Print all players who average more than 10 pts, 5 rebounds, and 5 assists.
for index, row in stats.iterrows():
    if (row["PTS"] > 10 and
        row["TRB"] > 5 and
        row["AST"] > 5):
        print(row["Player"], row["Tm"]);