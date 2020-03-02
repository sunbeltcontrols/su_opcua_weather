import logging
import asyncio
import configparser
import requests
from requests.exceptions import HTTPError
from asyncua import ua, Server

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger('asyncua')

def update_weather(location):
    
    '''this is a function that does stuff'''
    config = configparser.ConfigParser()
    #api = config.read('config.ini')
    api = 'f56ac88892eec5419c9bbb7333b689ab'
    pressure = 999
    temperature = 999
    humidity = 999
    wind_speed = 999
    try:
        url = "https://api.openweathermap.org/data/2.5/weather?q={}&units=imperial&appid={}".format(location, api)
        r = requests.get(url)
        r.raise_for_status()
    except HTTPError as http_err:
        print('openweather api not available')
    except Exception as err:
        print('aww snap something borked!')
    else:
        print('Successfully grabbed weather data')
        pressure = r.json()['main']['pressure'] / 33.864
        temperature = r.json()['main']['temp']
        humidity = r.json()['main']['humidity']
        wind_speed = r.json()['wind']['speed']

    return pressure, temperature, humidity, wind_speed
async def main():
    # setup our server
    server = Server()
    await server.init()
    server.set_endpoint('opc.tcp://localhost:4840/sunbeltOPC/server/')
    # setup our own namespace, not really necessary but should as spec
    uri = 'http://examples.freeopcua.github.io'
    idx = await server.register_namespace(uri)
    # get Objects node, this is where we should put our nodes
    objects = server.get_objects_node()

    # Gather updated values from OpenWeather Map api for mapping.
    pressure = 999
    temperature = 999
    humidity = 999
    wind_speed = 999

    # populating our address space
    root_obj = await objects.add_object(idx, 'Weather Data')

    # define variables wanted by the server here.
    w_pressure = await root_obj.add_variable(idx, 'Pressure', pressure)
    w_temperature = await root_obj.add_variable(idx, 'Temperature', temperature)
    w_humidity = await root_obj.add_variable(idx, 'Humidity', humidity)
    w_wind_speed = await root_obj.add_variable(idx, 'Wind Speed', wind_speed)

    # define variables that you may want to be writable by niagara here
    w_location = await root_obj.add_variable(idx, 'Location', 'Santa Clara, US')

    # Set variables from above to be writable by clients
    await w_location.set_writable()

    _logger.info('Starting server!')
    async with server:
        while True:
            await asyncio.sleep(10)
            loc = await w_location.read_value()
            weather = update_weather(loc)
            await w_pressure.set_value(weather[0])
            await w_temperature.set_value(weather[1])
            await w_humidity.set_value(weather[2])
            await w_wind_speed.set_value(weather[3])

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    # loop.set_debug(True)
    loop.run_until_complete(main())
    loop.close()