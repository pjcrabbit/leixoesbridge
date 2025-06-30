import asyncio
import websockets
import json
from datetime import datetime, timezone
import os
from shapely.geometry import Point
from shapely.geometry import shape
import requests
from bs4 import BeautifulSoup
import platform


API_KEY = "8a25ca745ce2307fc791fcd10a83851c27734793"

# ToDo - Have a file with a list of ports and their characteristics and replace this code with port selection

port_area =     {
      "type": "Feature",
      "properties": {},
      "geometry": {
        "coordinates": [
          [
            [
              -8.683796418916245,
              41.195703008376
            ],
            [
              -8.695040395252704,
              41.18922375503655
            ],
            [
              -8.695570168079087,
              41.189763353527184
            ],
            [
              -8.700338330772865,
              41.18683230489282
            ],
            [
              -8.699547036046255,
              41.18624165434201
            ],
            [
              -8.702492588169378,
              41.184359805095966
            ],
            [
              -8.703934154493652,
              41.185496938801066
            ],
            [
              -8.70320787863804,
              41.1859861660424
            ],
            [
              -8.705005486238093,
              41.18745301653021
            ],
            [
              -8.712137813479757,
              41.18339230640922
            ],
            [
              -8.708312879730556,
              41.17256320380238
            ],
            [
              -8.69703450067098,
              41.17738269456848
            ],
            [
              -8.69980296531503,
              41.180088929994355
            ],
            [
              -8.695746046468997,
              41.182183926515506
            ],
            [
              -8.698573020443035,
              41.18478350827863
            ],
            [
              -8.69201722958121,
              41.189149380708756
            ],
            [
              -8.686956418401678,
              41.1890909004664
            ],
            [
              -8.68544591515149,
              41.190175462148915
            ],
            [
              -8.687546028260016,
              41.191768250515224
            ],
            [
              -8.6825163892575,
              41.19464817000079
            ],
            [
              -8.683796418916245,
              41.195703008376
            ]
          ]
        ],
        "type": "Polygon"
      }
    }

inner_space = {
      "type": "Feature",
      "properties": {},
      "geometry": {
        "coordinates": [
          [
            [
              -8.692200139036402,
              41.18940021272073
            ],
            [
              -8.68724344872885,
              41.18940021272073
            ],
            [
              -8.685821907358275,
              41.19030105884303
            ],
            [
              -8.687692356530789,
              41.19187750973148
            ],
            [
              -8.68282918868178,
              41.19477695421077
            ],
            [
              -8.683747873911898,
              41.195742345515356
            ],
            [
              -8.693089566350949,
              41.19014153667624
            ],
            [
              -8.692200139036402,
              41.18940021272073
            ]
          ]
        ],
        "type": "Polygon"
      }
    }

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

  url = "https://livedata.apdl.pt/api/manoeuvres/filter/planned"
  body = {
          "search":"",
          "locode":"PTLEI",
          "dateFields":["datetime"],
          "initialSortBy":[
            {
              "key":"datetime",
              "order":"asc"
              }
            ],
          "searchFields":[
            "process_number",
            "name",
            "imo",
            "loa",
            "beam",
            "gt",
            "customs_ship",
            "ship_type",
            "type",
            "datetime"
            ],
          "per_page":100,
          "page":1,
          "sortBy":"datetime",
          "sortOrder":"asc"
  }

  response = requests.post(url, json=body)

  table = json.loads(response.text)

  table_data = []
  for item in table["data"]:
    ShipName = item["name"]
    manoeuvre = item["type"]
    dock = item["berth_location"].upper()
    if dock in docks:
      if manoeuvre == "Sair":
        manoeuvre_type = "out"
        m_time = item["etd"]
      elif manoeuvre == "Mudança":
        manoeuvre_type = "change"
        m_time = item["etd"]
      else:
        manoeuvre_type = "in"
        m_time = item["eta"]
      date = item["datetime"]
      if manoeuvre_type != "change":
        table_data.append([ShipName, manoeuvre_type, dock, m_time, date])

  return table_data

def in_area(polygon, position):

    polygon = shape(polygon["geometry"])

    # Create a Point object for the given position
    point = Point(position[1], position[0])  # Note the order (longitude, latitude)

    # Check if the point is inside the polygon
    return polygon.contains(point)

async def monitor_ships(ships_to_watch):
  async with websockets.connect("wss://stream.aisstream.io/v0/stream") as websocket:
      # Prepare subscription for your region
      subscribe_message = {
          "APIKey": API_KEY,
          "BoundingBoxes": [[[40, -10], [45, -5]]],
          "FilterMessageTypes": ["PositionReport"]
      }
      await websocket.send(json.dumps(subscribe_message))

      ship_names = []

      for ship in ships_to_watch:
        ship_names.append(ship[0])

      bridge_state = False
      crossing_ship = None

      while True:
          message_json = await websocket.recv()
          message = json.loads(message_json)
          message_type = message["MessageType"]
          ship_name = message["MetaData"]["ShipName"].strip()
          ship_id = message["MetaData"]["MMSI"]

          #Check if ship is already at destination
          #TBD

          # Check if this ship is in your list of interest
          for ship_info in ships_to_watch:
              if ship_name == ship_info[0]:  # ship_info[0] is ShipName
                  in_or_out = ship_info[1]  # "in" or "out"
                  if in_or_out == "in":
                      check_area = entry_area
                      crossing_heading = 50
                  else:
                      check_area = exit_area
                      crossing_heading = 230

                  # Extract position and other data
                  latitude = message["MetaData"]["latitude"]
                  longitude = message["MetaData"]["longitude"]
                  position = [latitude, longitude]
                  sog = message["Message"][message_type]["Sog"]
                  cog = message["Message"][message_type]["Cog"]

                  curr_time = datetime.now().strftime("%b%d %H:%M:%S")

                  dock_state = in_area(check_area, position)
                  if not bridge_state:
                      print(curr_time, "- Ship", ship_name, "is about to cross bridge. SoG:", sog, "CoG:", cog)
                      if dock_state and sog > 1.5 and (crossing_heading - 10 < cog < crossing_heading + 10):
                          print(curr_time, "- Bridge is open for the passage of", ship_name)
                          bridge_state = True
                          crossing_ship = ship_name
                  if bridge_state and crossing_ship == ship_name:
                      has_crossed = not in_area(check_area, position)
                      if has_crossed:
                          bridge_state = False
                          print(curr_time, "- Bridge has closed")
                          crossing_ship = None

if __name__ == "__main__":
  ships = get_next_crossing(inner_docks)
  for ship in ships:
      print(ship[0], ship[1], ship[2], ship[3])
  try:
    asyncio.run(monitor_ships(ships))
  except KeyboardInterrupt:
    print("Terminating program. Bye.")