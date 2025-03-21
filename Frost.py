import requests
import json
import os
import sys
from html.parser import HTMLParser

api_key = "x-api-key"
url = "fleet"

headers = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "content-type": "application/json",
    "origin": "origin url here",
    "referer": "referer url here",
    "x-api-key": api_key
}

ASCII_ART = """
   __            _
  / _|_ _ ___ __| |_ 
 |  _| '_/ _ (_-<  _|
 |_| |_| \___/__/\__|
"""

class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.logged_in = None
        self.username = None
        self.user_id = None
        self.platform = None
        self.created = None
        self.last_login = None
        self.api_key = None
        self.discord_id = None
        self.permissions = {}

    def handle_data(self, data):
        cleaned_data = data.strip()
        if cleaned_data and '"loggedIn"' in cleaned_data and '"userData"' in cleaned_data:
            try:
                json_data = json.loads(cleaned_data)
                self.logged_in = json_data.get("loggedIn", False)
                user_data = json_data.get("userData", {})

                self.username = user_data.get("username")
                self.user_id = user_data.get("user_id")
                self.discord_id = user_data.get("discord_id")
                self.platform = user_data.get("platform")
                self.created = user_data.get("created")
                self.last_login = user_data.get("last_login")
                self.api_key = json_data.get("apiKey")

                for perm in json_data.get("permissions", []):
                    fleet_id = perm.get("fleet_id", "GLOBAL")
                    permission = perm["permission"]
                    if fleet_id not in self.permissions:
                        self.permissions[fleet_id] = []
                    self.permissions[fleet_id].append(permission)
            except json.JSONDecodeError:
                pass

def clear_terminal():
    os.system('clear' if os.name != 'nt' else 'cls')

def get_key():
    return input()[0].lower()

def prompt(question):
    print(f"{question} (y/n): ", end="", flush=True)
    response = get_key()
    print(response)
    return response

def save_data(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=2)
    print(f"Data saved to {filename}")

def display_logo():
    print(ASCII_ART)

def fetch_data(quickfetch=False):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        if quickfetch:
            display_offline = False
            display_config = False
            show_ids = False
            only_active = True
        else:
            save_raw = prompt("Save raw data?") == 'y'
            if save_raw:
                save_data("fleet_data.json", data)
                print("\nFull data saved to fleet_data.json")
                input("\nPress Enter to continue...")
                return

            display_offline = prompt("Display offline servers?") == 'y'
            show_ids = prompt("Do you want to see Fleet/Station IDs?") == 'y'
            display_config = prompt("Display config data?") == 'y'
            only_active = not display_offline and prompt("Only show servers w/ player counts>0?") == 'y'

        filtered_servers = []
        for fleet in data.get("items", []):
            for station in fleet.get("stations", []):
                if (display_offline or station.get("online", False)) and \
                   (not only_active or station.get("player_count", 0) > 0):
                    
                    server_info = {
                        "fleet_id": fleet["fleet_id"],
                        "fleet_name": fleet["fleet_name"],
                        "station_id": station["station_id"],
                        "station_name": station["station_name"],
                        "region": station["region"],
                        "ip": station["ip"],
                        "version": station["version"],
                        "player_count": station["player_count"],
                        "online": station["online"]
                    }

                    if display_config:
                        server_info["config"] = fleet.get("config", {})

                    filtered_servers.append(server_info)

        if filtered_servers:
            for server in filtered_servers:
                print("\n    ", end="")
                
                if show_ids:
                    print(f"Fleet ID: {server['fleet_id']}")
                    print(f"    Fleet Name: {server['fleet_name']}")
                    print(f"    Station ID: {server['station_id']}")
                    print(f"    Station Name: {server['station_name']}")
                else:
                    print(f"Fleet Name: {server['fleet_name']}")
                    print(f"    Station Name: {server['station_name']}")

                print(f"    Region: {server['region']}")
                print(f"    IP: {server['ip']}")
                print(f"    Version/Netcl: {server['version']}")
                print(f"    Player Count: {server['player_count']}")
                print(f"    Online: {server['online']}")

                if display_config:
                    print(f"    Config: {json.dumps(server.get('config', {}), indent=2)}")

        else:
            print("No servers match the selected filters.")

    except requests.exceptions.RequestException as e:
        print(f"Network error occurred: {e}")

    input("\nPress Enter to return to the servers menu...")

def info():
    clear_terminal()
    display_logo()
    print("Info:\n")
    print("[1] Servers: Quickfetch, Howmanyspace, Server-Get, Server Search")
    print("[2] API Details: API Key, Server Auth, Perms linked to API Key")
    print("[3] Info: Feature info & credits")
    print("[4] Exit: Ends script & returns to terminal")
    print("\nCreated by KingAflak\nVersion 1.0")
    input("\nPress Enter to return to the menu...")

def howmanyspace():
    print("Fetching online servers...\n")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        fleet_data = {}
        total_players = 0

        for fleet in data.get("items", []):
            for station in fleet.get("stations", []):
                if station.get("online", False):
                    fleet_name = fleet["fleet_name"]
                    if fleet_name not in fleet_data:
                        fleet_data[fleet_name] = {
                            "stations": [],
                            "total_players": 0
                        }

                    player_count = station["player_count"]
                    fleet_data[fleet_name]["stations"].append({
                        "station_name": station["station_name"],
                        "region": station["region"],
                        "player_count": player_count,
                        "version": station["version"]
                    })
                    fleet_data[fleet_name]["total_players"] += player_count
                    total_players += player_count

        print(f"Total Players: {total_players}\n")
        for fleet_name, fleet_info in fleet_data.items():
            print(f"Fleet Name: {fleet_name} (Total Players: {fleet_info['total_players']})")
            for station in fleet_info["stations"]:
                print(f"    Station Name: {station['station_name']}")
                print(f"    Region: {station['region']}")
                print(f"    Player Count: {station['player_count']}")
                print(f"    Version: {station['version']}")
            print("-" * 30)

    except requests.exceptions.RequestException as e:
        print(f"Network error occurred: {e}")

    input("\nPress Enter to return to the servers menu...")

def fastspacefetch():
    print("Fetching online servers...\n")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        fleet_data = {}
        total_players = 0

        for fleet in data.get("items", []):
            for station in fleet.get("stations", []):
                if station.get("online", False):
                    fleet_name = fleet["fleet_name"]
                    if fleet_name not in fleet_data:
                        fleet_data[fleet_name] = {
                            "stations": [],
                            "total_players": 0
                        }

                    player_count = station["player_count"]
                    fleet_data[fleet_name]["stations"].append({
                        "station_name": station["station_name"],
                        "player_count": player_count
                    })
                    fleet_data[fleet_name]["total_players"] += player_count
                    total_players += player_count

        print(f"Total Players: {total_players}\n")
        for fleet_name, fleet_info in fleet_data.items():
            print(f"Fleet Name: {fleet_name} (Total Players: {fleet_info['total_players']})")
            for station in fleet_info["stations"]:
                print(f"    Station Name: {station['station_name']}")
                print(f"    Player Count: {station['player_count']}")
            print("-" * 30)

    except requests.exceptions.RequestException as e:
        print(f"Network error occurred: {e}")

    input("\nPress Enter to return to the servers menu...")

def quickfetch():
    fetch_data(quickfetch=True)

def scraprun_check():
    clear_terminal()
    display_logo()
    print("Scraprun Check\n")

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        sort_by_scraprun = prompt("Would you like to sort by Scraprun: Open?") == 'y'

        filtered_servers = []
        for fleet in data.get("items", []):
            for station in fleet.get("stations", []):
                if not station.get("online", False):
                    continue

                config = fleet.get("config", {})
                scraprun_open = config.get("loadedgamemodes.scraprunprime.modulestate.dashboardconfigoverrides.bscraprunopen", False)

                if sort_by_scraprun and not scraprun_open:
                    continue

                server_info = {
                    "fleet_name": fleet["fleet_name"],
                    "station_name": station["station_name"],
                    "scraprun_status": "Open" if scraprun_open else "Closed",
                    "version": station["version"],
                    "player_count": station["player_count"]
                }
                filtered_servers.append(server_info)

        if filtered_servers:
            print("\nFiltered Data:")
            for server in filtered_servers:
                print(f"\nFleet Name: {server['fleet_name']}")
                print(f"Station Name: {server['station_name']}")
                print(f"Scraprun Status: {server['scraprun_status']}")
                print(f"Version: {server['version']}")
                print(f"Player Count: {server['player_count']}")
        else:
            print("No servers match the selected filters.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")

    input("\nPress Enter to return to the servers menu...")

def api_details(first_call=True):
    url = "URL HERE REPLACE"
    headers = {
        "Cookie": f"meta_session=lmfaodashboarddoesntcareabouttheseskullemojiiiiii;dashboard_api_key={api_key}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        parser = MyHTMLParser()
        parser.feed(response.text)

        if first_call:
            return parser.username
        else:
            print(f"API Key: {api_key}")
            print(f"API Key is active. Username: {parser.username}.")
            print(f"User ID: {parser.user_id}")
            print(f"Platform: {parser.platform}")
            print(f"Created: {parser.created}")
            print(f"Last Login: {parser.last_login}")
            print(f"Discord ID: {parser.discord_id} (Discord User ID)")

            for fleet_id, permissions in parser.permissions.items():
                print(f"\nFleet Id: {fleet_id}")
                print(f"Permissions: {', '.join(permissions)}")

        input("\nPress Enter to return to the menu...")
        return parser.username
    else:
        print(f"Failed to fetch page: {response.status_code}")
        return None

def server_search():
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        search_fleet_name = input("Enter Fleet Name (or press Enter to skip): ")
        search_fleet_id = input("Enter Fleet ID (or press Enter to skip): ")
        search_station_name = input("Enter Station Name (or press Enter to skip): ")
        search_station_id = input("Enter Station ID (or press Enter to skip): ")
        search_region = input("Enter Region (or press Enter to skip): ")
        search_ip = input("Enter IP (or press Enter to skip): ")
        search_config_data = input("Enter Config Data key (or press Enter to skip): ")

        only_online = input("Do you want to only see online servers? (y/n): ").strip().lower() == "y"

        query = {}
        
        if search_fleet_name:
            query["fleet_name"] = search_fleet_name
        if search_fleet_id:
            query["fleet_id"] = search_fleet_id
        if search_station_name:
            query["station_name"] = search_station_name
        if search_station_id:
            query["station_id"] = search_station_id
        if search_region:
            query["region"] = search_region
        if search_ip:
            query["ip"] = search_ip
        if search_config_data:
            query["config_data"] = search_config_data

        filtered_servers = []
        for fleet in data.get("items", []):
            for station in fleet.get("stations", []):
                matches_query = True
                for key, value in query.items():
                    if key == "config_data":
                        if value not in json.dumps(fleet.get("config", {})):
                            matches_query = False
                            break
                    elif key in station and station[key] != value:
                        matches_query = False
                        break
                    elif key in fleet and fleet[key] != value:
                        matches_query = False
                        break
                
                if only_online and not station.get("online", False):
                    continue

                if matches_query:
                    server_info = {
                        "fleet_id": fleet["fleet_id"],
                        "fleet_name": fleet["fleet_name"],
                        "station_id": station["station_id"],
                        "station_name": station["station_name"],
                        "region": station["region"],
                        "ip": station["ip"],
                        "version": station["version"],
                        "player_count": station["player_count"],
                        "online": station["online"]
                    }

                    if "config" in fleet:
                        server_info["config"] = fleet["config"]

                    filtered_servers.append(server_info)

        if filtered_servers:
            print("\nFiltered Data:")
            for server in filtered_servers:
                print(f"\nFleet Name: {server['fleet_name']}")
                print(f"    Station Name: {server['station_name']}")
                print(f"    Region: {server['region']}")
                print(f"    IP: {server['ip']}")
                print(f"    Version: {server['version']}")
                print(f"    Player Count: {server['player_count']}")
                print(f"    Online: {server['online']}")

                if "config" in server:
                    print(f"    Config: {json.dumps(server['config'], indent=2)}")
        else:
            print("No servers match the selected filters.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")

    input("\nPress Enter to return to the servers menu...")

def playercounts():
    clear_terminal()
    print("Fetching player counts...\n")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        fleet_data = {}
        total_players = 0

        for fleet in data.get("items", []):
            fleet_name = fleet["fleet_name"]
            fleet_player_count = sum(station["player_count"] for station in fleet.get("stations", []) if station.get("online", False))
            fleet_data[fleet_name] = fleet_player_count
            total_players += fleet_player_count

        for fleet_name, player_count in fleet_data.items():
            print(f"{fleet_name}: {player_count}")
        print("-" * 30)
        print(f"Total Players: {total_players}\n")

    except requests.exceptions.RequestException as e:
        print(f"Network error occurred: {e}")

    input("\nPress Enter to return to the servers menu...")

def server_menu(username):
    while True:
        clear_terminal()
        display_logo()
        print(f"Welcome {username}!\n")

        print("[1] Playercounts")
        print("[2] HowManySpace")
        print("[3] FastSpaceFetch")
        print("[4] Server Search")
        print("[5] Scraprun Check")
        print("[6] Raw Data Sort")
        print("[7] API Details")
        print("[8] Exit")

        choice = input("\nSelect an option: ").strip()

        clear_terminal()

        if choice == "1":
            playercounts()
        elif choice == "2":
            howmanyspace()
        elif choice == "3":
            fastspacefetch()
        elif choice == "4":
            server_search()
        elif choice == "5":
            scraprun_check()
        elif choice == "6":
            fetch_data()
        elif choice == "7":
            api_details(first_call=False)
        elif choice == "8":
            print("Exiting...")
            break
        else:
            print("Invalid option. Please try again.")

def main():
    username = api_details(first_call=True)
    server_menu(username)

if __name__ == "__main__":
    main()