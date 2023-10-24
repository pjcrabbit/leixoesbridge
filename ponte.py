import asyncio
import websockets
import json
from datetime import datetime, timezone
import os
from shapely.geometry import Point
from shapely.geometry import shape
import requests
from bs4 import BeautifulSoup

API_KEY = "8a25ca745ce2307fc791fcd10a83851c27734793"


entry_area = {
      "type": "Feature",
      "properties": {},
      "geometry": {
        "coordinates": [
          [
            [
              -8.69977142047847,
              41.18653663425994
            ],
            [
              -8.698149667143753,
              41.184939440324996
            ],
            [
              -8.689380186146991,
              41.189956909092075
            ],
            [
              -8.691282242528132,
              41.191508781035765
            ],
            [
              -8.69977142047847,
              41.18653663425994
            ]
          ]
        ],
        "type": "Polygon"
      }
    }

exit_area = {
      "type": "Feature",
      "properties": {},
      "geometry": {
        "coordinates": [
          [
            [
              -8.688779562400413,
              41.19281955559981
            ],
            [
              -8.698369930887765,
              41.18747082273967
            ],
            [
              -8.696908350721088,
              41.18596405854535
            ],
            [
              -8.687257917296165,
              41.191463580166385
            ],
            [
              -8.688779562400413,
              41.19281955559981
            ]
          ]
        ],
        "type": "Polygon"
      }
    }

inner_docks = [
	"TERMINAL DE CONTENTORES SUL",
	"DOCA 2 NORTE",
	"DOCA 2 SUL",
	"DOCA 4 NORTE"
]

bridge_state = False
crossing_ship = 999999


def get_next_crossing(docks):

	url = "https://siga.apdl.pt/site-apdl/planeamento/naviosmanoprev.jsp"

	# Send an HTTP GET request to the URL
	response = requests.get(url)

	# Check if the request was successful
	if response.status_code == 200:
	    # Parse the HTML content of the page
	    table = BeautifulSoup(response.text, "html.parser")

	    if True:
	        # Initialize a list to store the extracted data
	        table_data = []

	        # Extract the rows (tr) from the table
	        rows = table.find_all("tr")

	        for row in rows:
	            # Extract the columns (td) from each row
	            columns = row.find_all("td")
	            row_data = [column.get_text(strip=True) for column in columns]
	            table_data.append(row_data)

	        # Print or return the extracted table data
	        expected = table_data[2:len(table_data) - 1]


	    else:
	        print("Table not found")
	else:
	    print("Failed to retrieve the web page. Status code:", response.status_code)

def in_area(polygon, position):

    polygon = shape(polygon["geometry"])

    # Create a Point object for the given position
    point = Point(position[1], position[0])  # Note the order (longitude, latitude)

    # Check if the point is inside the polygon
    return polygon.contains(point)



async def connect_ais_stream():

    async with websockets.connect("wss://stream.aisstream.io/v0/stream") as websocket:
        bridge_state = False

        # Real code will go here

        ship_crossing = True
        crossing_ship = 275524000

        in_or_out = "out"

        # End of fake code


        if in_or_out == "in":

        	check_area = entry_area
        	crossing_heading = 50

        else:

        	check_area = exit_area
        	crossing_heading = 230

        subscribe_message = {"APIKey": API_KEY,  # Required !
                             "BoundingBoxes": [[[40, -10], [45, -5]]],
                             "FilterMessageTypes": ["PositionReport"]}

        subscribe_message_json = json.dumps(subscribe_message)
        await websocket.send(subscribe_message_json)

        async for message_json in websocket:
        	message = json.loads(message_json)
        	message_type = message["MessageType"]

        	ShipID = message["MetaData"]["MMSI"]
        	ShipName = message["MetaData"]["ShipName"].strip()
        	if len(ShipName) < 2:
        		ShipName = "--- Not Available ---"
        	latitude = message["MetaData"]["latitude"]
        	longitude = message["MetaData"]["longitude"]
        	position = [latitude, longitude]
        	Speed_over_Ground = message["Message"][message_type]["Sog"]
        	Course_over_Ground = message["Message"][message_type]["Cog"]

        	#data = str(ShipID) + " " + ShipName + " " + str(Speed_over_Ground) + " " + str(Course_over_Ground) + " " + dock_state
        	#print(data)

        	if ShipID == crossing_ship and ship_crossing:

        		dock_state = in_area(check_area, position)

	        	curr_time = datetime.now().strftime("%b%d %H:%M:%S")
	        	#os.system('clear')

	        	if not(bridge_state):
	        		print(curr_time, "- Ship", ShipName, "is about to cross the bridge. Sog:", Speed_over_Ground, "CoG:", Course_over_Ground)

	        	if not(bridge_state) and dock_state and Speed_over_Ground > 1.5 and Course_over_Ground > (crossing_heading - 10) and Course_over_Ground < (crossing_heading + 10):
	        		print(curr_time, "- Bridge is open for the passage of", ShipName)
	        		bridge_state = True

	        	if bridge_state:

	        		has_crossed = not(in_area(check_area, position))

	        		if has_crossed:
	        			bridge_state = False
	        			print(curr_time, "- Bridge has closed")
	        			ship_crossing = False
	        		else:
	        			print(curr_time, "- Ship", ShipName, "is crossing the bridge")


if __name__ == "__main__":
    asyncio.run(asyncio.run(connect_ais_stream()))