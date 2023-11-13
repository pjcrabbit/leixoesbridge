import asyncio
import websockets
import json
from datetime import datetime, timezone
import os
from shapely.geometry import Point
from shapely.geometry import shape
import platform


API_KEY = "8a25ca745ce2307fc791fcd10a83851c27734793"

expire_time = 600

list_of_ships = {}

#############   Porto de Leixões   #############

port_vicinity_NW_corner = [41.800000, -10.000000]
port_vicinity_SE_corner = [40.500000, -8.600000]

dock_NE_corner = [41.19674105986371, -8.681732638743597]
dock_SW_corner = [41.17105757969003, -8.7122483762669]

port_geojson = {
  "type": "Feature",
  "properties": {},
  "geometry": {
    "coordinates": [
      [
            [
              -8.707946761917299,
              41.172705945251835
            ],
            [
              -8.697526902616346,
              41.17852056691086
            ],
            [
              -8.698964124588883,
              41.180109356295134
            ],
            [
              -8.696179507016666,
              41.18190092362099
            ],
            [
              -8.698065860856047,
              41.183726243698686
            ],
            [
              -8.69721251030964,
              41.18426706950689
            ],
            [
              -8.69779638173577,
              41.18477408964566
            ],
            [
              -8.692092407032021,
              41.18879631030288
            ],
            [
              -8.687062130128112,
              41.18872871199741
            ],
            [
              -8.684951210355706,
              41.19008066485307
            ],
            [
              -8.68710704331454,
              41.191702971429805
            ],
            [
              -8.681672547731068,
              41.19501505586692
            ],
            [
              -8.683289422450173,
              41.19640067412692
            ],
            [
              -8.700805565241012,
              41.18619372514951
            ],
            [
              -8.703994401492821,
              41.188289321308105
            ],
            [
              -8.711135598169136,
              41.184131863473596
            ],
            [
              -8.71212368827483,
              41.182441764503636
            ],
            [
              -8.707946761917299,
              41.172705945251835
            ]
      ]
    ],
    "type": "Polygon"
  }
}

#################################################

port_vicinity = [[port_vicinity_NW_corner,port_vicinity_SE_corner]]

dock = [[dock_SW_corner, dock_NE_corner]]


def prRed(skk): print("\033[91m {}\033[00m" .format(skk))
def prGreen(skk): print("\033[92m {}\033[00m" .format(skk))
def prYellow(skk): print("\033[93m {}\033[00m" .format(skk))
def prLightPurple(skk): print("\033[94m {}\033[00m" .format(skk))
def prPurple(skk): print("\033[95m {}\033[00m" .format(skk))
def prCyan(skk): print("\033[96m {}\033[00m" .format(skk))
def prLightGray(skk): print("\033[97m {}\033[00m" .format(skk))
def prBlack(skk): print("\033[98m {}\033[00m" .format(skk))

def in_area(polygon, position):

    polygon = shape(polygon["geometry"])

    # Create a Point object for the given position
    point = Point(position[1], position[0])  # Note the order (longitude, latitude)

    # Check if the point is inside the polygon
    return polygon.contains(point)


def print_list_of_ships(list_of_ships):


    #Pretty print of ship list

    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

    count = 0

    prLightGray("+----+----------------+----------------+---------------+--------------------------+-----------+-----------+-------+---------+")
    prLightGray("|  # |   First Seen   |   Last Seen    |    Ship ID    |         Ship Name        | Latitude  | Longitude |  SoG  | In Port |")
    prLightGray("+----+----------------+----------------+---------------+--------------------------+-----------+-----------+-------+---------+")

    for ship in list_of_ships:

        attributes = list_of_ships[ship]

        fs = attributes[0].strftime("%b%d %H:%M:%S")
        ls = attributes[1].strftime("%b%d %H:%M:%S")
        Id = str(attributes[2])
        
        num_spaces = 24 - len(attributes[3])
        Nm = f"{attributes[3]}{num_spaces * ' '}"

        Lt = str(format(attributes[4][0], ".6f"))
        Lg = str(format(attributes[4][1], ".6f"))

        sog = attributes[5]
        sog_len = len(str(sog))
        if sog_len == 3 or sog_len == 1:
            Sg = str(format(sog, ".2f"))
        else:
            Sg = str(format(sog, ".1f"))

        Ip = attributes[6]

        count += 1

        ct = str(count)

        if len(ct) == 1:
            ct = " " + ct

        toPrint = "| " + ct + " | " + fs + " | " + ls + " |   " + Id + "   | " + Nm + " | " + Lt + " | " + Lg + " | " + Sg + "  |   " + Ip + "   |"

        prCyan(toPrint)

    prLightGray("+----+----------------+----------------+---------------+--------------------------+-----------+-----------+-------+---------+")



def check_expired_ships(list_to_check, expire_time):

    #returns a list of expired ship IDs, i.e., ships that haven't been updated for more than 'expire_time' seconds

    ships_to_remove = []

    result_list = list_to_check.copy()
    current_time = datetime.now()

    for ship in list_to_check:
        attributes = list_to_check[ship]

        time_since_update = current_time - attributes[1]
        if time_since_update.total_seconds() > expire_time:
            ships_to_remove.append(ship)

    return ships_to_remove




async def connect_ais_stream():

    async with websockets.connect("wss://stream.aisstream.io/v0/stream") as websocket:
        subscribe_message = {"APIKey": API_KEY,  # Required !
                             "BoundingBoxes": port_vicinity} # Required!
                             #"FilterMessageTypes": ["PositionReport"] } # Optional!

        subscribe_message_json = json.dumps(subscribe_message)
        await websocket.send(subscribe_message_json)

        async for message_json in websocket:

            message = json.loads(message_json)
            message_type = message["MessageType"]


            if "Position" in message_type:

                ShipID = message["MetaData"]["MMSI"]
                ShipName = message["MetaData"]["ShipName"].strip()
                if len(ShipName) < 2:
                    ShipName = "--- Not Available ---"
                latitude = message["MetaData"]["latitude"]
                longitude = message["MetaData"]["longitude"]
                position = [latitude, longitude]
                Speed_over_Ground = message["Message"][message_type]["Sog"]

                #Check if ship is in port
                if in_area(port_geojson, position):
                    dock_state = "Yes"
                else:
                    dock_state = "No "

                #Check if ship is known
                if ShipID in list_of_ships.keys():
                    #This is a known ship
                    last_seen = datetime.now()#.strftime("%b%d %H:%M:%S")
                    ShipAttributes = [list_of_ships[ShipID][0], last_seen, ShipID, ShipName, position, Speed_over_Ground, dock_state]
                else:
                    first_seen = datetime.now()#.strftime("%b%d %H:%M:%S")
                    last_seen = first_seen
                    ShipAttributes = [first_seen, last_seen, ShipID, ShipName, position, Speed_over_Ground, dock_state]


                list_of_ships.update({ShipID: ShipAttributes})

                expired_ships = check_expired_ships(list_of_ships, expire_time)

                for ship in expired_ships:
                    if ship in list_of_ships:
                        list_of_ships.pop(ship)

                print_list_of_ships(list_of_ships)




if __name__ == "__main__":
    try:
        asyncio.run(asyncio.run(connect_ais_stream()))

    except KeyboardInterrupt:
        # Handle Ctrl+C here (e.g., cleanup, logging)
        prGreen("Ctrl+C detected. Cleaning up...")

    except ConnectionResetError:

        prRed("The connection has been reset. Program terminated")
        print("")

    except Exception as e:
        message = "An exception of type " + str(type(e)) + " occurred:" + "\n"
        prRed(message)
        prYellow(str(e))
        print("")
