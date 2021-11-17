import pandas
import matplotlib.pyplot as plt
import matplotlib as mpl
import sqlite3
cities = ["Carlsbad", "Del-Mar", "Solana-Beach", "Encinitas", "Carmel-Valley"]

# con = sqlite3.connect('sandiegorealestate.db')
# cur = con.cursor()

def show_graph(con):
    fig, ax = plt.subplots()
    ax.ticklabel_format(style='plain')
    plt.xticks(rotation=45)
    ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('${x:,.0f}'))
    for city in cities:
        city_query = f"SELECT * FROM averages WHERE city = '{city}'"
        city_data = pandas.read_sql_query(city_query, con)
        plt.plot(city_data['date'], city_data['listing_price'], label=city)
    plt.legend(fontsize=10)

    plt.show()

# con.close()