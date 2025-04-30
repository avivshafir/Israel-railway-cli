# Railway CLI

A command-line interface tool for searching Israel Railways train routes.

## Installation

1. Ensure you have Python 3.11+ installed
2. Install dependencies:
   ```
   pip install fire israel-rail-api pytz rich
   ```

## Usage

### Find Routes by Hour (Fixed Stations)

Search for train routes between Ra'anana West and Tel Aviv HaShalom at a specific hour:

```
python main.py find_routes_by_hour [HOUR] [--debug=DEBUG]
```

Example:

```
python main.py find_routes_by_hour 9
```

This will display all routes departing at 9:00 AM in both directions:

- From Ra'anana West to Tel Aviv HaShalom (displayed in green)
- From Tel Aviv HaShalom to Ra'anana West (displayed in blue)

### Find Routes Between Any Stations

Search for train routes between any two stations:

```
python main.py find_routes [ORIGIN] [DESTINATION] [HOUR] [--date=DATE] [--debug=DEBUG]
```

Example:

```
python main.py find_routes "Tel Aviv HaShalom" "Jerusalem Navon" 10
```

This will display all routes from Tel Aviv HaShalom to Jerusalem Navon departing at 10:00 AM.

## Display Format

The results are shown in beautifully formatted tables with the following information:

- Departure time
- Arrival time
- Journey duration
- Train numbers for each segment
- Number of transfers (or "Direct" for direct routes)
- Status indicators (crowding level, accessibility)
- Transfer details (for routes with changes), including:
  - Transfer station name
  - Arrival and departure times at the transfer station
  - Platform information
  - Wait time between trains

For the first route found, the tool also displays a detailed station-by-station breakdown showing all stops, arrival/departure times, and platforms.

## Parameters

- `hour`: The hour of departure (0-23)
- `origin`: The name of the origin station (English or Hebrew)
- `destination`: The name of the destination station (English or Hebrew)
- `date`: Optional date in YYYY-MM-DD format (defaults to current date)
- `debug`: Whether to show debug information about train and route structures (true/false)

## Features

- Beautiful, color-coded terminal output using the Rich library
- Flexible search allowing any origin and destination station
- Station name support in both English and Hebrew
- Automatic conversion between station codes and names
- Routes are displayed in organized tables sorted by departure time
- Journey duration is calculated and displayed in a human-readable format
- Train numbers are displayed for each route segment
- Crowding level indicators showing how busy each train is
- Accessibility information for handicap-accessible trains
- Detailed transfer information showing where and when to change trains
- Platform numbers for all stations and transfers
- Wait time calculation between connecting trains
- Full route details showing all stations on a journey
- Debug mode to help investigate API data structures
- Fast querying by including the hour in the API request

## Notes

- The tool supports over 20 popular Israel Railways stations with automatic Hebrew translation.
- If a station name isn't recognized, it will be passed to the API as-is.
- If no routes are found at the specified hour, an appropriate message is displayed.
- Error messages are clearly highlighted for troubleshooting.
- Use debug mode (`--debug=True`) to see detailed information about train objects.

## Examples

Search for routes from Herzliya to Beer Sheva at 8:00 AM:

```
python main.py find_routes "Herzliya" "Beer Sheva Center" 8
```

Search for routes from Tel Aviv University to Haifa on a specific date:

```
python main.py find_routes "Tel Aviv University" "Haifa Center" 16 --date=2025-05-10
```

View debug information about train objects:

```
python main.py find_routes "Jerusalem Navon" "Herzliya" 12 --debug=True
```
