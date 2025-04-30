# Railway CLI

A command-line interface tool for searching Israel Railways train routes.

## Installation

### Prerequisites

This tool requires Python 3.11 or higher.

### Using pip

```bash
# Install from GitHub
pip install git+https://github.com/yourusername/railway-cli.git

# Or, after downloading, install from the local directory
cd railway-cli
pip install .

# For development mode (changes to code will be reflected without reinstalling)
pip install -e .
```

### Using uv (Faster Installation)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver:

```bash
# Install uv if you don't have it
pip install uv

# Install railway-cli with uv
uv pip install git+https://github.com/yourusername/railway-cli.git

# Or from local directory
cd railway-cli
uv pip install .

# For development mode
uv pip install -e .
```

### Using pipx (Isolated Environment)

[pipx](https://pypa.github.io/pipx/) installs packages in isolated environments to avoid dependency conflicts:

```bash
# Install pipx if you don't have it
pip install pipx
pipx ensurepath

# Install railway-cli with pipx
pipx install git+https://github.com/yourusername/railway-cli.git

# Or from local directory
cd railway-cli
pipx install .
```

## Usage

Once installed, you can use the `railwaycli` command from anywhere.

### Find Routes Between Default Stations (Ra'anana West and Tel Aviv HaShalom)

```bash
# Find routes at 9:00
railwaycli find_routes_by_hour 9
```

### Find Routes Between Custom Stations

```bash
# Find routes between custom stations at 10:00
railwaycli find_routes_by_hour 10 "Herzliya" "Tel Aviv University"

# Using named parameters
railwaycli find_routes_by_hour 15 --origin="Jerusalem Navon" --destination="Beer Sheva Center"
```

### Find Routes Between Any Stations (Alternative Method)

```bash
railwaycli find_routes "Tel Aviv HaShalom" "Jerusalem Navon" 10
```

### Additional Options

- Set a specific date:

  ```bash
  railwaycli find_routes "Herzliya" "Beer Sheva Center" 8 --date=2025-06-01
  ```

## Example Output

Here's what the output looks like when searching for routes between Ra'anana West and Tel Aviv HaShalom:

```
╭─────────────────────────────────────────────────────────────────────────────────────────╮
│ Searching routes for 2025-04-30 at 09:00                                                │
╰─────────────────────────────────────────────────────────────────────────────────────────╯

╭─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│                                                    Routes from Ra'anana West to Tel Aviv HaShalom                                                                │
├───────────┬───────────┬───────────┬───────────┬───────────┬─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Departure │ Arrival   │ Duration  │ Train #   │ Transfers │ Transfer Details                                                                                     │
├───────────┼───────────┼───────────┼───────────┼───────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 09:03     │ 09:22     │ 19m       │ 651       │ Direct    │ -                                                                                                    │
├───────────┼───────────┼───────────┼───────────┼───────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 09:33     │ 09:52     │ 19m       │ 653       │ Direct    │ -                                                                                                    │
╰───────────┴───────────┴───────────┴───────────┴───────────┴─────────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│                                                    Routes from Tel Aviv HaShalom to Ra'anana West                                                                │
├───────────┬───────────┬───────────┬───────────┬───────────┬─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Departure │ Arrival   │ Duration  │ Train #   │ Transfers │ Transfer Details                                                                                     │
├───────────┼───────────┼───────────┼───────────┼───────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 09:07     │ 09:28     │ 21m       │ 650       │ Direct    │ -                                                                                                    │
├───────────┼───────────┼───────────┼───────────┼───────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 09:37     │ 09:58     │ 21m       │ 652       │ Direct    │ -                                                                                                    │
╰───────────┴───────────┴───────────┴───────────┴───────────┴─────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

Here's an example with a transfer:

```
╭──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│                                                      Routes from Jerusalem Navon to Beer Sheva Center                                                                  │
├───────────┬───────────┬───────────┬───────────┬───────────┬──────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Departure │ Arrival   │ Duration  │ Train #   │ Transfers │ Transfer Details                                                                                          │
├───────────┼───────────┼───────────┼───────────┼───────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 11:34     │ 13:53     │ 2h 19m    │ 724, 961  │ 1         │ Tel Aviv HaHagana: Train 724 → Train 961                                                                  │
│           │           │           │           │           │   Arrive: 12:44 (platform 4)                                                                               │
│           │           │           │           │           │   Depart: 12:51 (platform 2)                                                                               │
│           │           │           │           │           │   Wait: 7m                                                                                                 │
╰───────────┴───────────┴───────────┴───────────┴───────────┴──────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Features

- Beautiful, color-coded terminal output with line separations
- Support for both English and Hebrew station names
- Station code to name conversion
- Detailed transfer information including train numbers and platforms
- Fast querying by hour
- Error handling and validation

## Dependencies

- fire - Command line interface generation
- israelrailapi - API client for Israel Railways
- pytz - Timezone handling
- rich - Terminal formatting and tables

## License

This project is licensed under the MIT License - see the LICENSE file for details.

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

## Notes

- The tool supports over 20 popular Israel Railways stations with automatic Hebrew translation.
- If a station name isn't recognized, it will be passed to the API as-is.
- If no routes are found at the specified hour, an appropriate message is displayed.
- Error messages are clearly highlighted for troubleshooting.

## Examples

Search for routes from Herzliya to Beer Sheva at 8:00 AM:

```
railwaycli find_routes "Herzliya" "Beer Sheva Center" 8
```

Search for routes from Tel Aviv University to Haifa on a specific date:

```
railwaycli find_routes "Tel Aviv University" "Haifa Center" 16 --date=2025-05-10
```
