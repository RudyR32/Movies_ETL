{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 55,
   "metadata": {},
   "outputs": [],
   "source": [
    "import json\n",
    "import pandas as pd\n",
    "import numpy as np\n",
    "import re\n",
    "from sqlalchemy import create_engine\n",
    "import psycopg2\n",
    "from config import db_password\n",
    "import time"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 56,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/plain": [
       "'C:/Users/rnrai/Desktop/UCB_Data_Analysis/Movies_ETL/wikipedia.movies.json'"
      ]
     },
     "execution_count": 56,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "# Load\n",
    "file_dir = 'C:/Users/rnrai/Desktop/UCB_Data_Analysis/Movies_ETL/'\n",
    "f'{file_dir}wikipedia.movies.json'"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 57,
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "C:\\Users\\rnrai\\Anaconda3\\lib\\site-packages\\IPython\\core\\interactiveshell.py:3058: DtypeWarning: Columns (10) have mixed types. Specify dtype option on import or set low_memory=False.\n",
      "  interactivity=interactivity, compiler=compiler, result=result)\n"
     ]
    }
   ],
   "source": [
    "with open(f'{file_dir}/wikipedia.movies.json', mode='r') as file:\n",
    "        wiki_movies_raw = json.load(file)\n",
    "kaggle_metadata = pd.read_csv(f'{file_dir}movies_metadata.csv')\n",
    "ratings = pd.read_csv(f'{file_dir}ratings.csv')"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 58,
   "metadata": {},
   "outputs": [],
   "source": [
    "wiki_movies = [movie for movie in wiki_movies_raw\n",
    "    if ('Director' in movie or 'Directed by' in movie)\n",
    "    and 'imdb_link' in movie\n",
    "    and 'No. of episodes' not in movie]"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 59,
   "metadata": {},
   "outputs": [],
   "source": [
    "def clean_movie(movie):\n",
    "    movie = dict(movie) #create a non-destructive copy\n",
    "    alt_titles = {}\n",
    "    # combibe alternate titles\n",
    "    for key in ['Also known as','Arabic','Cantonese','Chinese','French',\n",
    "                'Hangul','Hebrew','Hepburn','Japanese','Literally',\n",
    "                'Mandarin','McCune–Reischauer','Original title','Polish',\n",
    "                'Revised Romanization','Romanized','Russian',\n",
    "                'Simplified','Traditional','Yiddish']:\n",
    "        if key in movie:\n",
    "            alt_titles[key] = movie[key]\n",
    "            movie.pop(key)\n",
    "    if len(alt_titles) > 0:\n",
    "        movie['alt_titles'] = alt_titles \n",
    "    # merge column names\n",
    "    def change_column_name(old_name, new_name):\n",
    "        if old_name in movie:\n",
    "            movie[new_name] = movie.pop(old_name)\n",
    "    change_column_name('Adaptation by', 'Writer(s)')\n",
    "    change_column_name('Country of origin', 'Country')\n",
    "    change_column_name('Directed by', 'Director')\n",
    "    change_column_name('Distributed by', 'Distributor')\n",
    "    change_column_name('Edited by', 'Editor(s)')\n",
    "    change_column_name('Length', 'Running time')\n",
    "    change_column_name('Original release', 'Release date')\n",
    "    change_column_name('Music by', 'Composer(s)')\n",
    "    change_column_name('Produced by', 'Producer(s)')\n",
    "    change_column_name('Producer', 'Producer(s)')\n",
    "    change_column_name('Productioncompanies ', 'Production company(s)')\n",
    "    change_column_name('Productioncompany ', 'Production company(s)')\n",
    "    change_column_name('Released', 'Release Date')\n",
    "    change_column_name('Release Date', 'Release date')\n",
    "    change_column_name('Screen story by', 'Writer(s)')\n",
    "    change_column_name('Screenplay by', 'Writer(s)')\n",
    "    change_column_name('Story by', 'Writer(s)')\n",
    "    change_column_name('Theme music composer', 'Composer(s)')\n",
    "    change_column_name('Written by', 'Writer(s)')\n",
    "\n",
    "    \n",
    "    return movie"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 60,
   "metadata": {},
   "outputs": [],
   "source": [
    "clean_movies = [clean_movie(movie) for movie in wiki_movies]"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 61,
   "metadata": {},
   "outputs": [],
   "source": [
    "wiki_movies_df = pd.DataFrame(clean_movies)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 62,
   "metadata": {},
   "outputs": [],
   "source": [
    "# \"(tt\\d{7}}\" the {7} says to match the last thing exactly 7 times\n",
    "# doing this to get each individual movie with an IMDb \n",
    "# need to put an 'r' in front of the quotes because there is a backslash being used\n",
    "wiki_movies_df['imdb_id'] = wiki_movies_df['imdb_link'].str.extract(r'(tt\\d{7})')\n",
    "# Drop Duplicates\n",
    "wiki_movies_df.drop_duplicates(subset='imdb_id', inplace=True)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 63,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Getting rid of the columns where 90% of the values are null\n",
    "wiki_columns_to_keep = [column for column in wiki_movies_df.columns if wiki_movies_df[column].isnull().sum() < len(wiki_movies_df) * 0.9]\n",
    "wiki_movies_df = wiki_movies_df[wiki_columns_to_keep]"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 64,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Box Office\n",
    "# Remove Movies with no box office data\n",
    "box_office = wiki_movies_df['Box office'].dropna()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 65,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Use a simple space as our joining character and apply the join() function only when our data points are lists\n",
    "box_office = box_office.apply(lambda x: ' '.join(x) if type(x) == list else x)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 66,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Use a regular expresion to capture millions and billions in the Box office numbers\n",
    "form_one = r'\\$\\s*\\d+\\.?\\d*\\s*[mb]illi?on'"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 67,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/plain": [
       "3903"
      ]
     },
     "execution_count": 67,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "# count the number of box offices that match our first forms\n",
    "# flags ingnore case\n",
    "box_office.str.contains(form_one, flags=re.IGNORECASE).sum()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 68,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/plain": [
       "1559"
      ]
     },
     "execution_count": 68,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "# Create the form two variable\n",
    "# Next, create a reg. ex. that matches the form '$123,456,789'\n",
    "# Fixing pattern matches\n",
    "#   Some values have spaces in between the dollar sign and the number...just need to add '\\s*'\n",
    "#   Some values use a period as a thousands separator, not a comma, add in '[,\\.]'\n",
    "#   Need to add a negatice lookahead because we don't want to catch values like '1.234 billion'\n",
    "form_two = r'\\$\\s*\\d{1,3}(?:[,\\.]\\d{3})+(?!\\s[mb]illion)'\n",
    "box_office.str.contains(form_two, flags=re.IGNORECASE).sum()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 69,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Create Boolean series to catch what matches each of from 1 and form 2\n",
    "matches_form_one = box_office.str.contains(form_one, flags=re.IGNORECASE)\n",
    "matches_form_two = box_office.str.contains(form_two, flags=re.IGNORECASE)\n",
    "\n",
    "# # this will throw an error!\n",
    "# box_office[(not matches_form_one) and (not matches_form_two)]"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 70,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Solve values given as a range\n",
    "box_office = box_office.str.replace(r'\\$.*[-—–](?![a-z])', '$', regex=True)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 71,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/html": [
       "<div>\n",
       "<style scoped>\n",
       "    .dataframe tbody tr th:only-of-type {\n",
       "        vertical-align: middle;\n",
       "    }\n",
       "\n",
       "    .dataframe tbody tr th {\n",
       "        vertical-align: top;\n",
       "    }\n",
       "\n",
       "    .dataframe thead th {\n",
       "        text-align: right;\n",
       "    }\n",
       "</style>\n",
       "<table border=\"1\" class=\"dataframe\">\n",
       "  <thead>\n",
       "    <tr style=\"text-align: right;\">\n",
       "      <th></th>\n",
       "      <th>0</th>\n",
       "    </tr>\n",
       "  </thead>\n",
       "  <tbody>\n",
       "    <tr>\n",
       "      <td>0</td>\n",
       "      <td>$21.4 million</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <td>1</td>\n",
       "      <td>$2.7 million</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <td>2</td>\n",
       "      <td>$57,718,089</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <td>3</td>\n",
       "      <td>$7,331,647</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <td>4</td>\n",
       "      <td>$6,939,946</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <td>...</td>\n",
       "      <td>...</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <td>7070</td>\n",
       "      <td>$19.4 million</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <td>7071</td>\n",
       "      <td>$41.9 million</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <td>7072</td>\n",
       "      <td>$76.1 million</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <td>7073</td>\n",
       "      <td>$38.4 million</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <td>7074</td>\n",
       "      <td>$5.5 million</td>\n",
       "    </tr>\n",
       "  </tbody>\n",
       "</table>\n",
       "<p>5485 rows × 1 columns</p>\n",
       "</div>"
      ],
      "text/plain": [
       "                  0\n",
       "0     $21.4 million\n",
       "1      $2.7 million\n",
       "2       $57,718,089\n",
       "3        $7,331,647\n",
       "4        $6,939,946\n",
       "...             ...\n",
       "7070  $19.4 million\n",
       "7071  $41.9 million\n",
       "7072  $76.1 million\n",
       "7073  $38.4 million\n",
       "7074   $5.5 million\n",
       "\n",
       "[5485 rows x 1 columns]"
      ]
     },
     "execution_count": 71,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "#  Use the Extract method to extract date that only matches form 1 or foom 2\n",
    "box_office.str.extract(f'({form_one}|{form_two})')"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 72,
   "metadata": {},
   "outputs": [],
   "source": [
    "def parse_dollars(s):\n",
    "    # if s is not a string, return NaN\n",
    "    if type(s) != str:\n",
    "        return np.nan\n",
    "\n",
    "    # if input is of the form $###.# million\n",
    "    if re.match(r'\\$\\s*\\d+\\.?\\d*\\s*milli?on', s, flags=re.IGNORECASE):\n",
    "\n",
    "        # remove dollar sign and \" million\"\n",
    "        s = re.sub('\\$|\\s|[a-zA-Z]','', s)\n",
    "\n",
    "        # convert to float and multiply by a million\n",
    "        value = float(s) * 10**6\n",
    "\n",
    "        # return value\n",
    "        return value\n",
    "\n",
    "    # if input is of the form $###.# billion\n",
    "    elif re.match(r'\\$\\s*\\d+\\.?\\d*\\s*billi?on', s, flags=re.IGNORECASE):\n",
    "\n",
    "        # remove dollar sign and \" billion\"\n",
    "        s = re.sub('\\$|\\s|[a-zA-Z]','', s)\n",
    "\n",
    "        # convert to float and multiply by a billion\n",
    "        value = float(s) * 10**9\n",
    "\n",
    "        # return value\n",
    "        return value\n",
    "\n",
    "    # if input is of the form $###,###,###\n",
    "    elif re.match(r'\\$\\s*\\d{1,3}(?:[,\\.]\\d{3})+(?!\\s[mb]illion)', s, flags=re.IGNORECASE):\n",
    "\n",
    "        # remove dollar sign and commas\n",
    "        s = re.sub('\\$|,','', s)\n",
    "\n",
    "        # convert to float\n",
    "        value = float(s)\n",
    "\n",
    "        # return value\n",
    "        return value\n",
    "\n",
    "    # otherwise, return NaN\n",
    "    else:\n",
    "        return np.nan"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 73,
   "metadata": {},
   "outputs": [],
   "source": [
    "# # Now we can parse the box office values to numeric values\n",
    "#   Extract values from box_office using str.extract and apply parse_dollars to the first column of the dataframe\n",
    "wiki_movies_df['box_office'] = box_office.str.extract(f'({form_one}|{form_two})', flags=re.IGNORECASE)[0].apply(parse_dollars)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 74,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Drop the Box Office Column\n",
    "wiki_movies_df.drop('Box office', axis=1, inplace=True)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 75,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Create the Budget Variable\n",
    "budget = wiki_movies_df['Budget'].dropna()\n",
    "# Convert any lists to strings\n",
    "budget = budget.map(lambda x: ' '.join(x) if type(x) == list else x)\n",
    "# Then remove any values between a dollar sign and a hyphen (for budgets given in ranges)\n",
    "budget = budget.str.replace(r'\\$.*[-—–](?![a-z])', '$', regex=True)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 76,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Parse the Budget Data\n",
    "matches_form_one = budget.str.contains(form_one, flags=re.IGNORECASE)\n",
    "matches_form_two = budget.str.contains(form_two, flags=re.IGNORECASE)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 77,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Remove the citation references with the following\n",
    "budget = budget.str.replace(r'\\[\\d+\\]\\s*', '')"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 78,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Parse Budget Data to numeric values\n",
    "wiki_movies_df['budget'] = budget.str.extract(f'({form_one}|{form_two})', flags=re.IGNORECASE)[0].apply(parse_dollars)\n",
    "# Drop original Budget Column\n",
    "wiki_movies_df.drop('Budget', axis=1, inplace=True)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 79,
   "metadata": {},
   "outputs": [],
   "source": [
    "# make a variable that holds the non-null values of Release date in the DataFrame, converting lists to strings\n",
    "release_date = wiki_movies_df['Release date'].dropna().apply(lambda x: ' '.join(x) if type(x) == list else x)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 80,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Full month name, one- to two-digit day, four-digit year (i.e., January 1, 2000)\n",
    "# Four-digit year, two-digit month, two-digit day, with any separator (i.e., 2000-01-01)\n",
    "# Full month name, four-digit year (i.e., January 2000)\n",
    "# Four-digit year\n",
    "date_form_one = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\\s[123]\\d,\\s\\d{4}'\n",
    "date_form_two = r'\\d{4}.[01]\\d.[123]\\d'\n",
    "date_form_three = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\\s\\d{4}'\n",
    "date_form_four = r'\\d{4}'"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 81,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Use existing Datetime function\n",
    "wiki_movies_df['release_date'] = pd.to_datetime(release_date.str.extract(f'({date_form_one}|{date_form_two}|{date_form_three}|{date_form_four})')[0], infer_datetime_format=True)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 82,
   "metadata": {},
   "outputs": [],
   "source": [
    "# make a variable that holds the non-null values of Release date in the DataFrame, converting lists to strings\n",
    "running_time = wiki_movies_df['Running time'].dropna().apply(lambda x: ' '.join(x) if type(x) == list else x)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 83,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/plain": [
       "6877"
      ]
     },
     "execution_count": 83,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "# only mark the beginning of the string, and accept other abbreviations of “minutes” by only searching up to the letter “m.”\n",
    "running_time.str.contains(r'^\\d*\\s*m', flags=re.IGNORECASE).sum()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 84,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Match all the hors + minutes patterns with one regex\n",
    "# Start with one digit.\n",
    "# Have an optional space after the digit and before the letter “h.”\n",
    "# Capture all the possible abbreviations of “hour(s).” To do this, we’ll make every letter in “hours” optional except the “h.”\n",
    "# Have an optional space after the “hours” marker.\n",
    "# Have an optional number of digits for minutes.\n",
    "running_time_extract = running_time.str.extract(r'(\\d+)\\s*ho?u?r?s?\\s*(\\d*)|(\\d+)\\s*m')"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 85,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Use numeric()\n",
    "# Set error arguement to coerce, this will turn empty strings to NaN\n",
    "# we can then use 'fillna()' to change all of the NaN's to zero.\n",
    "running_time_extract = running_time_extract.apply(lambda col: pd.to_numeric(col, errors='coerce')).fillna(0)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 86,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Apply a function that will convert hour and minute capture groups to minutes\n",
    "wiki_movies_df['running_time'] = running_time_extract.apply(lambda row: row[0]*60 + row[1] if row[2] == 0 else row[2], axis=1)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 87,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Finally, we can drop Running time from the dataset with the following code\n",
    "wiki_movies_df.drop('Running time', axis=1, inplace=True)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 88,
   "metadata": {},
   "outputs": [],
   "source": [
    "# The following code will keep rows where the adult column is False, and then drop the adult column\n",
    "kaggle_metadata = kaggle_metadata[kaggle_metadata['adult'] == 'False'].drop('adult',axis='columns')\n",
    "# Error because the code was run twice and 'adult' had already been removed"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 89,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/plain": [
       "0        False\n",
       "1        False\n",
       "2        False\n",
       "3        False\n",
       "4        False\n",
       "         ...  \n",
       "45461    False\n",
       "45462    False\n",
       "45463    False\n",
       "45464    False\n",
       "45465    False\n",
       "Name: video, Length: 45454, dtype: bool"
      ]
     },
     "execution_count": 89,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "# convert the datatypes in 'video'\n",
    "kaggle_metadata['video'] == 'True'"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 90,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Assign Booleans just created back into 'video'\n",
    "kaggle_metadata['video'] = kaggle_metadata['video'] == 'True'"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 91,
   "metadata": {},
   "outputs": [],
   "source": [
    "# For the numeric columns, we can just use the to_numeric() method from Pandas. We’ll make sure the errors= argument is set to 'raise', so we’ll know if there’s any data that can’t be converted to numbers\n",
    "kaggle_metadata['budget'] = kaggle_metadata['budget'].astype(int)\n",
    "kaggle_metadata['id'] = pd.to_numeric(kaggle_metadata['id'], errors='raise')\n",
    "kaggle_metadata['popularity'] = pd.to_numeric(kaggle_metadata['popularity'], errors='raise')"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 92,
   "metadata": {},
   "outputs": [],
   "source": [
    "# use to_datetime to convert release date to datetime\n",
    "kaggle_metadata['release_date'] = pd.to_datetime(kaggle_metadata['release_date'])"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 93,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "<class 'pandas.core.frame.DataFrame'>\n",
      "RangeIndex: 26024289 entries, 0 to 26024288\n",
      "Data columns (total 4 columns):\n",
      "userId       26024289 non-null int64\n",
      "movieId      26024289 non-null int64\n",
      "rating       26024289 non-null float64\n",
      "timestamp    26024289 non-null int64\n",
      "dtypes: float64(1), int64(3)\n",
      "memory usage: 794.2 MB\n"
     ]
    }
   ],
   "source": [
    "# Set null counts to true in the ratings data\n",
    "ratings.info(null_counts=True)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 94,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/plain": [
       "0          2015-03-09 22:52:09\n",
       "1          2015-03-09 23:07:15\n",
       "2          2015-03-09 22:52:03\n",
       "3          2015-03-09 22:52:26\n",
       "4          2015-03-09 22:52:36\n",
       "                   ...        \n",
       "26024284   2009-10-31 23:26:04\n",
       "26024285   2009-10-31 23:33:52\n",
       "26024286   2009-10-31 23:29:24\n",
       "26024287   2009-11-01 00:06:30\n",
       "26024288   2009-10-31 23:30:58\n",
       "Name: timestamp, Length: 26024289, dtype: datetime64[ns]"
      ]
     },
     "execution_count": 94,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "# We’ll specify in to_datetime() that the origin is 'unix' and the time unit is seconds\n",
    "pd.to_datetime(ratings['timestamp'], unit='s')"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 95,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Assign to the timestamp Column\n",
    "ratings['timestamp'] = pd.to_datetime(ratings['timestamp'], unit='s')"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 96,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Print out a list of the columns so we can identify which ones are redundant\n",
    "# Use suffixes parameter to make it easier to identify which table the column came from\n",
    "movies_df = pd.merge(wiki_movies_df, kaggle_metadata, on='imdb_id', suffixes=['_wiki','_kaggle'])"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 97,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Competing data:\n",
    "# Wiki                     Movielens                Resolution\n",
    "#--------------------------------------------------------------------------\n",
    "# title_wiki               title_kaggle             Drop Wikipedia\n",
    "# running_time             runtime                  Keep Kaggle; fill in zeros with\n",
    "#                                                   Wikipedia data.\n",
    "# budget_wiki              budget_kaggle            Keep Kaggle; fill in zeros with\n",
    "#                                                   Wikipedia data.\n",
    "# box_office               revenue                  Keep Kaggle; fill in zeros with\n",
    "#                                                   Wikipedia data.\n",
    "# release_date_wiki        release_date_kaggle      Drop Wikipedia\n",
    "# Language                 original_language        Drop Wikipedia\n",
    "# Production company(s)    production_companies     Drop Wikipedia"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 98,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Put it all together\n",
    "# drop the title_wiki, release_date_wiki, Language, and Production company(s) columns\n",
    "movies_df.drop(columns=['title_wiki','release_date_wiki','Language','Production company(s)'], inplace=True)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 99,
   "metadata": {},
   "outputs": [],
   "source": [
    "#Create a function that fills in missing data for a column pair and then drops the redundant column\n",
    "def fill_missing_kaggle_data(df, kaggle_column, wiki_column):\n",
    "    df[kaggle_column] = df.apply(\n",
    "        lambda row: row[wiki_column] if row[kaggle_column] == 0 else row[kaggle_column]\n",
    "        , axis=1)\n",
    "    df.drop(columns=wiki_column, inplace=True)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 100,
   "metadata": {},
   "outputs": [],
   "source": [
    "# run the function for the pairs we decided to fill with zeros\n",
    "fill_missing_kaggle_data(movies_df, 'runtime', 'running_time')\n",
    "fill_missing_kaggle_data(movies_df, 'budget_kaggle', 'budget_wiki')\n",
    "fill_missing_kaggle_data(movies_df, 'revenue', 'box_office')"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 101,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Reoprder the columns\n",
    "movies_df = movies_df[['imdb_id','id','title_kaggle','original_title','tagline','belongs_to_collection','url','imdb_link','runtime','budget_kaggle','revenue','release_date_kaggle','popularity','vote_average','vote_count','genres','original_language','overview','spoken_languages','Country','production_companies','production_countries','Distributor','Producer(s)','Director','Starring','Cinematography','Editor(s)','Writer(s)','Composer(s)','Based on']]"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 102,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Rename the columns\n",
    "movies_df.rename({'id':'kaggle_id',\n",
    "                  'title_kaggle':'title',\n",
    "                  'url':'wikipedia_url',\n",
    "                  'budget_kaggle':'budget',\n",
    "                  'release_date_kaggle':'release_date',\n",
    "                  'Country':'country',\n",
    "                  'Distributor':'distributor',\n",
    "                  'Producer(s)':'producers',\n",
    "                  'Director':'director',\n",
    "                  'Starring':'starring',\n",
    "                  'Cinematography':'cinematography',\n",
    "                  'Editor(s)':'editors',\n",
    "                  'Writer(s)':'writers',\n",
    "                  'Composer(s)':'composers',\n",
    "                  'Based on':'based_on'\n",
    "                 }, axis='columns', inplace=True)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 103,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Use groupby on movieID and ratings to take a count of each group\n",
    "rating_counts = ratings.groupby(['movieId','rating'], as_index=False).count() \\\n",
    "                .rename({'userId':'count'}, axis=1) \\\n",
    "                .pivot(index='movieId',columns='rating', values='count')"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 104,
   "metadata": {},
   "outputs": [],
   "source": [
    "# prepend ratings to each column for readablity\n",
    "rating_counts.columns = ['rating_' + str(col) for col in rating_counts.columns]"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 105,
   "metadata": {},
   "outputs": [],
   "source": [
    "# use a left merge to merge movies_df and rating_df while keeping everything in movies_df\n",
    "movies_with_ratings_df = pd.merge(movies_df, rating_counts, left_on='kaggle_id', right_index=True, how='left')"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 106,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Fill in missing values with zeros\n",
    "movies_with_ratings_df[rating_counts.columns] = movies_with_ratings_df[rating_counts.columns].fillna(0)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 107,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Connect to pgAdmin\n",
    "db_string = f\"postgres://postgres:{db_password}@127.0.0.1:5432/movie_data\""
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 108,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Create the database engine\n",
    "engine = create_engine(db_string)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 111,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Importing Movie Data\n",
    "#To save the movies_df DataFrame to a SQL table, \n",
    "#we only have to specify the name of the table and the engine in the to_sql() method\n",
    "movies_df.to_sql(name='movies_challenge', con=engine)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 112,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "importing rows 0 to 1000000...Done. 111.53701448440552 total seconds elapsed\n",
      "importing rows 1000000 to 2000000...Done. 237.58666467666626 total seconds elapsed\n",
      "importing rows 2000000 to 3000000...Done. 359.5967438220978 total seconds elapsed\n",
      "importing rows 3000000 to 4000000...Done. 480.5820984840393 total seconds elapsed\n",
      "importing rows 4000000 to 5000000...Done. 597.3454449176788 total seconds elapsed\n",
      "importing rows 5000000 to 6000000...Done. 714.2941913604736 total seconds elapsed\n",
      "importing rows 6000000 to 7000000...Done. 826.0191740989685 total seconds elapsed\n",
      "importing rows 7000000 to 8000000...Done. 939.2050583362579 total seconds elapsed\n",
      "importing rows 8000000 to 9000000...Done. 1081.722154378891 total seconds elapsed\n",
      "importing rows 9000000 to 10000000...Done. 1213.2453224658966 total seconds elapsed\n",
      "importing rows 10000000 to 11000000...Done. 1343.8522017002106 total seconds elapsed\n",
      "importing rows 11000000 to 12000000...Done. 1488.3501620292664 total seconds elapsed\n",
      "importing rows 12000000 to 13000000...Done. 1626.529004573822 total seconds elapsed\n",
      "importing rows 13000000 to 14000000...Done. 1759.8077127933502 total seconds elapsed\n",
      "importing rows 14000000 to 15000000...Done. 1884.8284921646118 total seconds elapsed\n",
      "importing rows 15000000 to 16000000...Done. 2009.8775687217712 total seconds elapsed\n",
      "importing rows 16000000 to 17000000...Done. 2130.175847053528 total seconds elapsed\n",
      "importing rows 17000000 to 18000000...Done. 2261.156104326248 total seconds elapsed\n",
      "importing rows 18000000 to 19000000...Done. 2391.5740442276 total seconds elapsed\n",
      "importing rows 19000000 to 20000000...Done. 2520.449500799179 total seconds elapsed\n",
      "importing rows 20000000 to 21000000...Done. 2647.597357273102 total seconds elapsed\n",
      "importing rows 21000000 to 22000000...Done. 2771.534240961075 total seconds elapsed\n",
      "importing rows 22000000 to 23000000...Done. 2903.2057490348816 total seconds elapsed\n",
      "importing rows 23000000 to 24000000...Done. 3020.9844822883606 total seconds elapsed\n",
      "importing rows 24000000 to 25000000...Done. 3142.4449033737183 total seconds elapsed\n",
      "importing rows 25000000 to 26000000...Done. 3262.2243208885193 total seconds elapsed\n",
      "importing rows 26000000 to 26024289...Done. 3264.903149366379 total seconds elapsed\n"
     ]
    }
   ],
   "source": [
    "# Final step afet many iterations\n",
    "rows_imported = 0\n",
    "# get the start_time from time.time()\n",
    "start_time = time.time()\n",
    "for data in pd.read_csv(f'{file_dir}/ratings.csv', chunksize=1000000):\n",
    "    print(f'importing rows {rows_imported} to {rows_imported + len(data)}...', end='')\n",
    "    data.to_sql(name='ratings', con=engine, if_exists='append')\n",
    "    rows_imported += len(data)\n",
    "\n",
    "    # add elapsed time to final print out\n",
    "    print(f'Done. {time.time() - start_time} total seconds elapsed')"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.7.4"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 2
}
