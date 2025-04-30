# Railway CLI

A command-line interface tool for searching Israel Railways train routes.

## Installation

1. Ensure you have Python 3.11+ installed
2. Install dependencies:
   ```
   pip install fire israel-rail-api pytz rich
   ```

## Usage

### Find Routes by Hour

Search for train routes between Ra'anana West and Tel Aviv HaShalom at a specific hour:

```
python main.py find_routes_by_hour [HOUR]
```

Example:

```
python main.py find_routes_by_hour 9
```

This will display all routes departing at 9:00 AM in both directions:

- From Ra'anana West to Tel Aviv HaShalom (displayed in green)
- From Tel Aviv HaShalom to Ra'anana West (displayed in blue)

The results are shown in a beautifully formatted table with the following information:

- Departure time
- Arrival time
- Journey duration
- Number of transfers (or "Direct" for direct routes)

## Parameters

- `hour`: The hour of departure (0-23)

## Features

- Beautiful, color-coded terminal output using the Rich library
- Routes are displayed in separate tables by direction
- Tables are sorted by departure time
- Journey duration is calculated and displayed in a human-readable format
- Clear indication of transfer requirements
- Fast querying by including the hour in the API request

## Notes

- The tool searches for routes in both directions between Ra'anana West (רעננה מערב) and Tel Aviv HaShalom (תל אביב - השלום).
- If no routes are found at the specified hour, an appropriate message is displayed.
- Error messages are clearly highlighted for troubleshooting.
