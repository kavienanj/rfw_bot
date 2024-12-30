import pandas as pd
import sqlite3

# Load CSV file into DataFrame
df = pd.read_csv('data.csv')

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('data.db')

# Convert DataFrame to SQL table
df.to_sql('products', conn, if_exists='replace', index=False)

# Run a simple SQL query
query = """
SELECT *, Title_en as Title FROM products WHERE Taste LIKE '%Smoky%' AND Type = 'whisky' LIMIT 5
"""
result = pd.read_sql_query(query, conn)

# Print the result
print(result[['Title_en']])

# Close the connection
conn.close()
