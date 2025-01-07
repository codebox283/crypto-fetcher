from flask import Flask, render_template, send_file
import pandas as pd
import io
import requests

app = Flask(__name__)

# Global variable to store crypto data
crypto_data_cache = None

def fetch_crypto_data():
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=50&page=1&sparkline=false"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        return None

def perform_data_analysis(df):
    top_5 = df.nlargest(5, 'Market Capitalization')
    average_price = df['Current Price (USD)'].mean()
    highest_change = df['Price Change (24h, %)'].max()
    lowest_change = df['Price Change (24h, %)'].min()
    
    return top_5, average_price, highest_change, lowest_change

@app.route('/')
def index():
    global crypto_data_cache  # Use the global variable
    if crypto_data_cache is None:  # Fetch data only if not already cached
        crypto_data_cache = fetch_crypto_data()
    
    if crypto_data_cache:
        df = pd.DataFrame(crypto_data_cache)
        
        df['image'] = [coin['image'] for coin in crypto_data_cache]
        df = df[['image', 'name', 'symbol', 'current_price', 'market_cap', 'total_volume', 'price_change_percentage_24h']]
        df.columns = ['Image', 'Cryptocurrency Name', 'Symbol', 'Current Price (USD)', 'Market Capitalization', '24h Trading Volume', 'Price Change (24h, %)']
        
        top_5, average_price, highest_change, lowest_change = perform_data_analysis(df)

        html_table = df.to_html(classes='data', escape=False, formatters={'Image': lambda x: f'<img src="{x}" width="30" height="30"/>'})
        
        analysis_summary = {
            "Top 5 Cryptocurrencies": top_5.to_html(classes='data', escape=False, formatters={'Image': lambda x: f'<img src="{x}" width="30" height="30"/>'}),
            "Average Price": f"${average_price:.2f}",
            "Highest Price Change (24h)": f"{highest_change:.2f}%",
            "Lowest Price Change (24h)": f"{lowest_change:.2f}%"
        }

        return render_template('index.html', tables=[html_table], titles=df.columns.values, analysis=analysis_summary)
    else:
        return "Error fetching data"

@app.route('/download')
def download():
    global crypto_data_cache  # Use the cached data
    if crypto_data_cache:
        df = pd.DataFrame(crypto_data_cache)
        
        df = df[['name', 'symbol', 'current_price', 'market_cap', 'total_volume', 'price_change_percentage_24h']]
        df.columns = ['Cryptocurrency Name', 'Symbol', 'Current Price (USD)', 'Market Capitalization', '24h Trading Volume', 'Price Change (24h, %)']
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Crypto Data')
        
        output.seek(0)  # Move to the start of the BytesIO object
        
        return send_file(
            output,
            as_attachment=True,
            download_name="crypto_data.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        return "Error fetching data"

if __name__ == '__main__':
    app.run(debug=True)
