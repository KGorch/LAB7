import uvicorn
import psycopg2 as pg
from fastapi import FastAPI, HTTPException
from starlette.responses import JSONResponse
import re


app = FastAPI()

# Подключение к базе данных
conn = pg.connect(user='postgres', password='123', host='localhost', port='5432', database='LAB7')
cursor = conn.cursor()

def check(name):
    cursor.execute("""select id from public.currency_rates 
                            where base_currency = %s""", (name,))
    data_id=cursor.fetchall()
    data_id = re.sub(r"[^0-9]", r"", str(data_id))
    print(data_id)
    return (data_id)

def get(name,id):
    print(id,name)
    cursor.execute("""select rate from public.currency_rates_values 
                              where  currency_rate_id = %s and currency_code =%s""", (id,name,))
    data_id = cursor.fetchall()
    data_id = re.sub(r"[^0-9]", r"", str(data_id))


    return (data_id)


@app.get("/convert")
def convert_get(baseCurrency: str, convertedCurrency: str, sum: float):
    try:
        print(baseCurrency,convertedCurrency,sum)
        baseCurrency=int(check(baseCurrency))
        print (baseCurrency)
        convertedCurrency=int(get(convertedCurrency,baseCurrency))
        print(convertedCurrency)
        if convertedCurrency != 0 and baseCurrency !=0:
            res=convertedCurrency*sum
            return ({'converted': res})


    except:
        raise HTTPException(500)

if __name__ == '__main__':
    uvicorn.run(app, port=10610, host='localhost')