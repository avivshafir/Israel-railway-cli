# Railway CLI

A command-line interface tool for searching Israel Railways train routes.

## Installation

### Local Installation (Development Mode)

Clone the repository and install in development mode:

```bash
git clone https://github.com/yourusername/railway-cli.git
cd railway-cli
pip install -e .
```

### Global Installation

Install directly from the repository:

```bash
pip install git+https://github.com/yourusername/railway-cli.git
```

Or, after downloading, install from the local directory:

```bash
cd railway-cli
pip install .
```

## Usage

Once installed, you can use the `railwaycli` command from anywhere:

### Find Routes Between Ra'anana West and Tel Aviv HaShalom

```bash
railwaycli find_routes_by_hour 9
```

### Find Routes Between Any Stations

```bash
railwaycli find_routes "Tel Aviv HaShalom" "Jerusalem Navon" 10
```

### Additional Options

- Set a specific date:

  ```bash
  railwaycli find_routes "Herzliya" "Beer Sheva Center" 8 --date=2025-06-01
  ```

- Enable debug mode:
  ```bash
  railwaycli find_routes "Tel Aviv University" "Haifa Center" 16 --debug=True
  ```

## Features

- Beautiful, color-coded terminal output with line separations
- Support for both English and Hebrew station names
- Station code to name conversion
- Detailed transfer information including train numbers and platforms
- Fast querying by hour
- Error handling and validation

## Dependencies

- fire
- israelrailapi
- pytz
- rich
