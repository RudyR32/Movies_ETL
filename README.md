# Movies_ETL
## Project Overview
Amazing Prime is trying to improve there profit margains and is running a hackathon to figure out which low budget movies will be popular with users.  They have tasked you (Brita) with the task of creating a SQL datadase to make the data accessable to the participants.  You will us pandas and PostgresSQL to Extract, Transform and Load (ETL) from Wikipedia and Kaggle to create the data base.
## Challenge
### Assumptions
1.  The data sources did not change.  If they did then the code would need to be altered.<br/>
2.  The column names did not change.  Much of our cleaning used specific column names and any changes to those names would result in errors in our code.<br/>
3.  The Postgres user remains unchanged.  This code uses information specific to the user who wrote it and would not run if used with out editing by another user<br/>
4.  We need to assume that the datatypes in the columns that are not dropped remain the same.<br/>
5.  Several places throughout the code we specifically call out values(months, column name, languages, etc.) and our code is not designed to run without breaking in a situation where their is a new value or a miss spelling.  Example would be in the case of someone spelling a month wrong the code would error out.
