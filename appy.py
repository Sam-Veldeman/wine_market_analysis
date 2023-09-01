import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

# Connect to the SQLite database
conn = sqlite3.connect('./data/vivino.db')
cursor = conn.cursor()

# Query functions
def query_highlight_10_wines(min_ratings, max_price, min_count):
    query = """
    SELECT
        v.id, v.name AS vintage_name, v.ratings_average, v.year, v.price_euros, v.ratings_count, w.url
    FROM
        vintages AS v
        JOIN wines AS w ON v.wine_id = w.id
    WHERE
        v.ratings_average >= ? AND v.price_euros <= ?  AND v.ratings_count > ? AND v.year != 'N.V.' AND v.price_discounted_from IS NULL
    ORDER BY
        v.price_euros;
    """
    return conn.execute(query, (min_ratings, max_price, min_count)).fetchall()

def query_wines_with_taste_keywords():
    query = """
    SELECT w.name, (kw.group_name || '(' || k.name || ')') as group_name, sum(kw.count) 
    FROM wines w
    JOIN keywords_wine kw ON kw.wine_id = w.id
    JOIN keywords k ON k.id = kw.keyword_id
    WHERE w.id in (
        SELECT
            w.id
            FROM wines w
            JOIN keywords_wine kw ON kw.wine_id = w.id
            JOIN keywords k ON k.id = kw.keyword_id
            WHERE k.name in ('coffee','toast','green apple','cream','citrus')
            and kw.count > 10
            and kw.keyword_type = 'primary'
            GROUP BY w.id
            HAVING MAX(CASE WHEN k.name = 'coffee' THEN kw.group_name ELSE 0 END) <> 0 AND 
                MAX(CASE WHEN k.name = 'toast' THEN kw.group_name ELSE 0 END) <> 0 AND 
                MAX(CASE WHEN k.name = 'green apple' THEN kw.group_name ELSE 0 END) <> 0 AND 
                MAX(CASE WHEN k.name = 'cream' THEN kw.group_name ELSE 0 END) <> 0 AND 
                MAX(CASE WHEN k.name = 'citrus' THEN kw.group_name ELSE 0 END) <> 0
            ) and k.name in ('coffee','toast','green apple','cream','citrus')
                and kw.count > 10
                and kw.keyword_type = 'primary'
            GROUP BY w.name, kw.group_name
            ;
    """
    return conn.execute(query).fetchall()

def query_top5_wines_per_grape():
    query = """
    SELECT * FROM 
            (SELECT w.name, w.ratings_average, w.ratings_count, g.name
            FROM wines w
            JOIN regions r ON r.id = w.region_id
            JOIN countries c ON c.code = r.country_code
            JOIN most_used_grapes_per_country mg ON mg.country_code = c.code
            JOIN grapes g ON mg.grape_id = g.id
            WHERE mg.grape_id = 2 and w.ratings_count > 2000
            ORDER BY w.ratings_average DESC, w.ratings_count DESC
            LIMIT 5)

            UNION ALL

            SELECT * FROM 
            (SELECT w.name, w.ratings_average, w.ratings_count, g.name
            FROM wines w
            JOIN regions r ON r.id = w.region_id
            JOIN countries c ON c.code = r.country_code
            JOIN most_used_grapes_per_country mg ON mg.country_code = c.code
            JOIN grapes g ON mg.grape_id = g.id
            WHERE mg.grape_id = 5 and w.ratings_count > 2000
            ORDER BY w.ratings_average DESC, w.ratings_count DESC
            LIMIT 5) 

            UNION ALL

            SELECT * FROM 
            (SELECT w.name, w.ratings_average, w.ratings_count, g.name
            FROM wines w
            JOIN regions r ON r.id = w.region_id
            JOIN countries c ON c.code = r.country_code
            JOIN most_used_grapes_per_country mg ON mg.country_code = c.code
            JOIN grapes g ON mg.grape_id = g.id
            WHERE mg.grape_id = 10 and w.ratings_count > 2000
            ORDER BY w.ratings_average DESC, w.ratings_count DESC
            LIMIT 5)
            ;
    """
    return conn.execute(query).fetchall()

def query_top5_wines_cabernet_sauvignon():
    query = """
    SELECT w.name, w.ratings_average, w.ratings_count, g.name
            FROM wines w
            JOIN regions r ON r.id = w.region_id
            JOIN countries c ON c.code = r.country_code
            JOIN most_used_grapes_per_country mg ON mg.country_code = c.code
            JOIN grapes g ON mg.grape_id = g.id
            WHERE mg.grape_id = 2 and w.ratings_count > 2000
            ORDER BY w.ratings_average DESC, w.ratings_count DESC
            LIMIT 5
            ;
    """
    return conn.execute(query).fetchall()

# Streamlit app
def main():
    st.set_page_config(page_title='Vivino market analysis', page_icon=':wine_glass:', layout='wide')
    # Title
    st.markdown("""<h1 style='text-align: center; margin-bottom: 50px; margin-top: 10px;'>Vivino Market Analysis</h1>""", unsafe_allow_html=True)
        
    # Select query
    query_option = st.sidebar.selectbox("Query selection:", ["Highlight 10 wines", "Wines with taste keywords", "Top 5 wines for top 3 grapes", "Top 5 wines with Cabernet Sauvignon", "Country Leaderboards", "Focus on Argentina"])
    
    if query_option == "Highlight 10 wines":
        # Add sliders
        min_count = st.slider('Minimum Ratings Count', min_value=0.0, max_value=37000.0, step=100.0, value=30.0)
        min_ratings = st.slider('Minimum Ratings Average', min_value=0.0, max_value=5.0, step=0.1, value=0.0)
        max_price = st.slider('Maximum Price (Euros)', min_value=0, max_value=100, step=1, value=100)
        result = query_highlight_10_wines(min_ratings, max_price, min_count)
        # Convert the result to a DataFrame and create a new Plotly visualization
        columns = ['id', 'vintage_name', 'ratings_average', 'year', 'price_euros', 'ratings_count', 'url']
        df = pd.DataFrame(result, columns=columns)
        # Filter the data based on slider values
        filtered_df = df[
            (df['ratings_count'] >= min_count) &
            (df['ratings_average'] >= min_ratings) &
            (df['price_euros'] <= max_price)
        ]
        # Display only the first 10 rows
        st.dataframe(filtered_df.head(10))
    elif query_option == "Wines with taste keywords":
        result = query_wines_with_taste_keywords()
         # Convert the result to a DataFrame
        columns = ['name_wine', 'group_name', 'count']
        df = pd.DataFrame(result, columns=columns)
        st.header('Wines that have all identified primary keywords provided in the data.')
        st.header('Conclusion is that this mainly serves for "Brute Champagne" wines')
        fig1 = px.histogram(df, x="name_wine", y="count", color="group_name", marginal="rug",
                   hover_data=df.columns)
        #Plotting the chart
        st.plotly_chart(fig1, use_container_width=True)
    elif query_option == "Top 5 wines for top 3 grapes":
        result = query_top5_wines_per_grape()
         # Convert the result to a DataFrame
        columns = ['wine', 'ratings_average', 'ratings_count', 'grape']
        df = pd.DataFrame(result, columns=columns)
        st.header('The 5 best rated wines, based on the top 3 most common grapes gloabally.')
        fig2 = px.histogram(df, x="wine", y="ratings_average", color="grape", marginal="rug",
                   hover_data=df.columns, histfunc='avg')
        #Plotting the chart
        st.plotly_chart(fig2, use_container_width=True)
    elif query_option == "Top 5 wines with Cabernet Sauvignon":
        result = query_top5_wines_cabernet_sauvignon()
         # Convert the result to a DataFrame
        columns = ['wine', 'ratings_average', 'ratings_count', 'grape']
        df = pd.DataFrame(result, columns=columns)
        st.header('This is specially for our VIP client.')
        st.header('It shows our selection of the top 5 recommended wines of "Cabernet Sauvignon".')
        fig4 = px.histogram(df, x="wine", y="ratings_average", color="grape", marginal="rug",
                   hover_data=df.columns)
        #Plotting the chart
        st.plotly_chart(fig4, use_container_width=True)
    elif query_option == "Country Leaderboards":
        st.header("Country Leaderboards")
        image_path = './output/CountryLeaderboard.png'
        st.image(image_path, use_column_width=True)
    elif query_option == "Focus on Argentina":
        st.header("Country Leaderboards")
        image_path = './output/FocusOnArgentina.png'
        st.image(image_path, use_column_width=True)
    # Small text at the bottom
    st.markdown("""<p style='text-align: right; font-size: small;'>By César Mendoza, Fré Van Oers and Sam Veldeman</p>""", unsafe_allow_html=True)

    # Close the database connection
    conn.close()

if __name__ == '__main__':
    main()
