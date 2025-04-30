"""Railway CLI implementation."""

import israelrailapi
from datetime import datetime
import pytz
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import re
import json


class RailwayCLI:
    """CLI tool for searching train routes in Israel."""

    def __init__(self):
        self.schedule = israelrailapi.TrainSchedule()
        self.console = Console()

    def find_routes_by_hour(
        self, hour, origin="Ra'anana West", destination="Tel Aviv HaShalom"
    ):
        """Find train routes between two stations at a specific hour.

        Args:
            hour: The hour (0-23) to search for routes
            origin: The origin station (default: Ra'anana West)
            destination: The destination station (default: Tel Aviv HaShalom)

        Returns:
            Displays formatted train routes in both directions
        """
        # Validate hour
        try:
            hour = int(hour)
            if not 0 <= hour <= 23:
                raise ValueError("Hour must be between 0 and 23")
        except ValueError as e:
            self.console.print(f"[bold red]Error:[/bold red] {str(e)}", style="red")
            return

        # Get current date in Israel timezone
        israel_tz = pytz.timezone("Asia/Jerusalem")
        search_date = datetime.now(israel_tz).date().strftime("%Y-%m-%d")

        # Print date information
        self.console.print(
            Panel(
                f"[bold blue]Searching routes for {search_date} at {hour:02d}:00[/bold blue]"
            )
        )

        # Define the stations with both Hebrew and English names for display
        stations = {
            "origin": {"he": self._get_hebrew_station_name(origin), "en": origin},
            "destination": {
                "he": self._get_hebrew_station_name(destination),
                "en": destination,
            },
        }

        results = self._query_routes(stations, search_date, hour)
        self._display_results(results, stations, hour)

    def _query_routes(self, stations, search_date, hour):
        """Query routes between stations for a specific date and hour."""
        results = {"outbound": [], "inbound": []}

        # Helper function to query and filter routes for a specific direction
        def query_direction(origin, destination, result_key):
            try:
                # Query with the hour for better filtering
                routes = self.schedule.query(
                    origin, destination, search_date, f"{hour:02d}:00"
                )

                # Filter routes to only include those in the requested hour
                for route in routes:
                    if hasattr(route, "start_time") and isinstance(
                        route.start_time, str
                    ):
                        departure_hour = int(route.start_time.split("T")[1][:2])
                        if departure_hour == hour:
                            results[result_key].append(route)
            except Exception as e:
                self.console.print(
                    f"[bold red]Error querying routes from {origin} to {destination}:[/bold red] {str(e)}"
                )

        # Query both directions
        query_direction(
            stations["origin"]["he"],
            stations["destination"]["he"],
            "outbound",
        )
        query_direction(
            stations["destination"]["he"],
            stations["origin"]["he"],
            "inbound",
        )

        return results

    def _display_results(self, results, stations, hour):
        """Display train route results in a formatted table."""
        # Display routes from origin to destination
        self._display_direction_table(
            results["outbound"],
            stations["origin"]["en"],
            stations["destination"]["en"],
            "green",
        )

        # Display routes from destination to origin
        self._display_direction_table(
            results["inbound"],
            stations["destination"]["en"],
            stations["origin"]["en"],
            "blue",
        )

    def _display_direction_table(self, routes, origin, destination, color="white"):
        """Create and display a table for train routes in one direction."""
        if not routes:
            title = f"[bold {color}]No routes from {origin} to {destination} at the specified hour[/bold {color}]"
            self.console.print(Panel(title, border_style=color))
            return

        # Create a table for this direction with increased width
        title = f"[bold {color}]Routes from {origin} to {destination}[/bold {color}]"
        table = Table(
            title=title,
            show_header=True,
            header_style=f"bold {color}",
            width=120,
            show_lines=True,  # Add line separators between rows
        )

        # Add columns
        table.add_column("Departure", style=f"dim {color}")
        table.add_column("Arrival", style=f"dim {color}")
        table.add_column("Duration", style=f"{color}")
        table.add_column("Train #", style=f"dim {color}")
        table.add_column("Transfers", justify="center", style=f"{color}")
        table.add_column(
            "Transfer Details", style=f"italic {color}", no_wrap=False, width=60
        )

        # Sort routes by departure time
        sorted_routes = sorted(routes, key=lambda r: r.start_time)

        # Add route data to the table
        for route in sorted_routes:
            # Extract time information
            start_time = self._format_time(route.start_time)
            end_time = self._format_time(route.end_time)
            duration = self._calculate_duration(route.start_time, route.end_time)

            # Count number of trains to determine transfers
            transfers = len(route.trains) - 1
            transfers_text = f"{transfers}" if transfers > 0 else "Direct"

            # Get train numbers
            train_numbers = self._get_train_numbers(route)

            # Get transfer details if there's a transfer
            transfer_details = (
                self._get_transfer_details(route) if transfers > 0 else "-"
            )

            # Add row to table
            table.add_row(
                start_time,
                end_time,
                duration,
                train_numbers,
                transfers_text,
                transfer_details,
            )

        # Print the table with increased width
        self.console.print(Panel(table, border_style=color, width=120))

    def _get_route_status(self, route):
        """Get status information for a route."""
        status_parts = []

        # Check for crowding information
        for train in route.trains:
            if hasattr(train, "data") and isinstance(train.data, dict):
                # Check for accessibility
                if "handicap" in train.data and train.data["handicap"]:
                    status_parts.append("[bold green]♿[/bold green]")  # Accessible

                # Check for crowding
                if "crowded" in train.data:
                    crowded_status = train.data["crowded"]
                    if crowded_status in ["EMPTY", "LOW"]:
                        status_parts.append(
                            "[bold green]▁[/bold green]"
                        )  # Low crowding
                    elif crowded_status == "MEDIUM":
                        status_parts.append(
                            "[bold yellow]▃[/bold yellow]"
                        )  # Medium crowding
                    elif crowded_status in ["HIGH", "FULL"]:
                        status_parts.append("[bold red]▆[/bold red]")  # High crowding

                # If we found at least one status, we can stop
                if status_parts:
                    break

        return " ".join(status_parts) if status_parts else "-"

    def _display_route_stations(self, route, color="white"):
        """Display all stations on a route."""
        # Check if the route has trains with routeStations data
        if not hasattr(route, "trains") or not route.trains:
            return

        # Find a train with routeStations information
        route_stations = None
        for train in route.trains:
            if (
                hasattr(train, "data")
                and isinstance(train.data, dict)
                and "routeStations" in train.data
            ):
                route_stations = train.data["routeStations"]
                break

        if not route_stations:
            return

        # Create a table for the stations
        table = Table(
            title=f"[bold {color}]Full Route Stations[/bold {color}]",
            show_header=True,
            header_style=f"bold {color}",
        )

        # Add columns
        table.add_column("Station", style=f"dim {color}")
        table.add_column("Arrival", style=f"dim {color}")
        table.add_column("Departure", style=f"dim {color}")
        table.add_column("Platform", style=f"dim {color}")

        # Add station data to the table
        try:
            for station in route_stations:
                station_name = self._get_station_name(
                    str(station.get("stationId", "")), hebrew=False
                )
                arrival = self._format_time(station.get("arrivalTime", ""))
                departure = self._format_time(station.get("departureTime", ""))
                platform = station.get("platform", "-")

                table.add_row(
                    station_name,
                    arrival if arrival != "N/A" else "-",
                    departure if departure != "N/A" else "-",
                    str(platform),
                )

            # Print the table
            self.console.print(Panel(table, border_style=color))
        except Exception:
            # If there's an error, silently skip the station display
            pass

    def _get_train_numbers(self, route):
        """Extract train numbers from the route."""
        if not hasattr(route, "trains") or not route.trains:
            return "N/A"

        train_nums = []
        for train in route.trains:
            # Get train number from each train in the route
            train_num = self._get_single_train_number(train)
            if train_num != "Unknown Train":
                # Extract just the number from "Train #XXX"
                train_nums.append(train_num.replace("Train #", ""))
            else:
                train_nums.append("?")

        return ", ".join(filter(None, train_nums))

    def _get_station_name(self, station_code, hebrew=True):
        """Convert station code to station name.

        Args:
            station_code: The station code to convert
            hebrew: Whether to include the Hebrew name
        """
        # Dictionary of known station codes to station names
        station_codes = {
            # These are the station codes from the debug output
            # Add more as you discover them
            "3500": {"he": "תל אביב - השלום", "en": "Tel Aviv HaShalom"},
            "4600": {"he": "רעננה מערב", "en": "Ra'anana West"},
            "3700": {"he": "תל אביב - ההגנה", "en": "Tel Aviv HaHagana"},
            "3600": {"he": "תל אביב - מרכז", "en": "Tel Aviv Center"},
            "3400": {"he": "תל אביב - אוניברסיטה", "en": "Tel Aviv University"},
            "3300": {"he": "הרצליה", "en": "Herzliya"},
            "4640": {"he": "רעננה דרום", "en": "Ra'anana South"},
            "2100": {"he": "חיפה - מרכז", "en": "Haifa Center"},
            "2200": {"he": "חיפה - בת גלים", "en": "Haifa Bat Galim"},
            "2300": {"he": "חיפה - חוף הכרמל", "en": "Haifa Hof HaCarmel"},
            "1300": {"he": "עכו", "en": "Akko"},
            "1400": {"he": "נהריה", "en": "Nahariya"},
            "6500": {"he": "ירושלים - יצחק נבון", "en": "Jerusalem Navon"},
            "5200": {"he": "אשקלון", "en": "Ashkelon"},
            "5300": {"he": "באר שבע - צפון", "en": "Beer Sheva North"},
            "5400": {"he": "באר שבע - מרכז", "en": "Beer Sheva Center"},
            "4800": {"he": "לוד", "en": "Lod"},
            "4900": {"he": "רמלה", "en": "Ramla"},
            "5000": {"he": "בית שמש", "en": "Beit Shemesh"},
        }

        # Return the station name if found, otherwise return the code
        if station_code in station_codes:
            if hebrew:
                return f"{station_codes[station_code]['he']} ({station_codes[station_code]['en']})"
            else:
                return station_codes[station_code]["en"]
        return f"Station {station_code}"

    def _get_transfer_details(self, route):
        """Extract transfer details from a route with transfers."""
        if not hasattr(route, "trains") or len(route.trains) <= 1:
            return "-"

        transfer_details = []

        for i in range(len(route.trains) - 1):
            current_train = route.trains[i]
            next_train = route.trains[i + 1]

            # Skip if we don't have basic transfer station information
            if not hasattr(current_train, "dst") or not hasattr(next_train, "src"):
                transfer_details.append("Change trains (details unavailable)")
                continue

            # Get transfer station name (English only)
            station_code = str(current_train.dst)
            station_name = self._get_station_name(station_code, hebrew=False)

            # Get train numbers for both trains
            from_train = self._get_single_train_number(current_train).replace(
                "Train #", ""
            )
            to_train = self._get_single_train_number(next_train).replace("Train #", "")

            # Build transfer text
            transfer_text = [f"{station_name}: Train {from_train} → Train {to_train}"]

            # Add time information if available
            if hasattr(current_train, "arrival") and hasattr(next_train, "departure"):
                # Format arrival/departure times
                arrival_time = self._format_time(current_train.arrival)
                departure_time = self._format_time(next_train.departure)

                # Get platform information
                arrival_platform = (
                    f"platform {current_train.dst_platform}"
                    if hasattr(current_train, "dst_platform")
                    and current_train.dst_platform
                    else "?"
                )
                departure_platform = (
                    f"platform {next_train.platform}"
                    if hasattr(next_train, "platform") and next_train.platform
                    else "?"
                )

                # Calculate wait time
                wait_minutes = self._calculate_wait_time(
                    current_train.arrival, next_train.departure
                )

                # Add time and platform details
                transfer_text.append(f"  Arrive: {arrival_time} ({arrival_platform})")
                transfer_text.append(
                    f"  Depart: {departure_time} ({departure_platform})"
                )
                transfer_text.append(f"  Wait: {wait_minutes}m")

            transfer_details.append("\n".join(transfer_text))

        return "\n\n".join(transfer_details)

    def _get_single_train_number(self, train):
        """Extract a single train number from a train object."""
        # Check data dictionary first (most common location)
        if (
            hasattr(train, "data")
            and isinstance(train.data, dict)
            and "trainNumber" in train.data
        ):
            return f"Train #{train.data['trainNumber']}"

        # Check direct attributes on the train object
        for attr in ["train_number", "trainNumber", "number", "trainno", "train_no"]:
            if hasattr(train, attr):
                return f"Train #{getattr(train, attr)}"

        return "Unknown Train"

    def _format_time(self, time_str):
        """Format ISO time string to HH:MM."""
        if not time_str or not isinstance(time_str, str):
            return "N/A"

        try:
            # Extract time part (HH:MM) from ISO format (YYYY-MM-DDTHH:MM:SS)
            return time_str.split("T")[1][:5]
        except (IndexError, AttributeError):
            return "N/A"

    def _calculate_duration(self, start_time, end_time):
        """Calculate and format journey duration in minutes."""
        if not all(
            [
                start_time,
                end_time,
                isinstance(start_time, str),
                isinstance(end_time, str),
            ]
        ):
            return "N/A"

        try:
            # Parse ISO datetime strings
            start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))

            # Calculate duration in minutes
            duration_minutes = (end - start).total_seconds() / 60

            # Format as HH:MM if hour > 0, otherwise just MM minutes
            if duration_minutes >= 60:
                hours, mins = divmod(int(duration_minutes), 60)
                return f"{hours}h {mins}m"
            else:
                return f"{int(duration_minutes)}m"
        except (ValueError, TypeError):
            return "N/A"

    def _calculate_wait_time(self, arrival_time, departure_time):
        """Calculate wait time between arrival and departure in minutes."""
        if not all(
            [
                arrival_time,
                departure_time,
                isinstance(arrival_time, str),
                isinstance(departure_time, str),
            ]
        ):
            return 0

        try:
            # Parse ISO datetime strings
            arrival = datetime.fromisoformat(arrival_time.replace("Z", "+00:00"))
            departure = datetime.fromisoformat(departure_time.replace("Z", "+00:00"))

            # Calculate and return wait time in minutes
            return max(0, int((departure - arrival).total_seconds() / 60))
        except (ValueError, TypeError):
            return 0

    def find_routes(self, origin, destination, hour, date=None):
        """Find train routes between any two stations at a specific hour."""
        # Validate hour
        try:
            hour = int(hour)
            if not 0 <= hour <= 23:
                raise ValueError("Hour must be between 0 and 23")
        except ValueError as e:
            self.console.print(f"[bold red]Error:[/bold red] {str(e)}", style="red")
            return

        # Get or validate date
        if date is None:
            # Use current date in Israel timezone
            israel_tz = pytz.timezone("Asia/Jerusalem")
            search_date = datetime.now(israel_tz).date().strftime("%Y-%m-%d")
        else:
            # Validate date format
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
                self.console.print(
                    f"[bold red]Error:[/bold red] Date must be in YYYY-MM-DD format",
                    style="red",
                )
                return
            search_date = date

        # Show search info
        self.console.print(
            Panel(
                f"[bold blue]Searching routes from {origin} to {destination} for {search_date} at {hour:02d}:00[/bold blue]"
            )
        )

        # Convert station names to Hebrew for the API
        origin_he = self._get_hebrew_station_name(origin)
        destination_he = self._get_hebrew_station_name(destination)

        # Query the routes
        try:
            # Query the API
            routes = self.schedule.query(
                origin_he, destination_he, search_date, f"{hour:02d}:00"
            )

            # Filter routes by the requested hour
            filtered_routes = []
            for route in routes:
                if hasattr(route, "start_time") and isinstance(route.start_time, str):
                    departure_hour = int(route.start_time.split("T")[1][:2])
                    if departure_hour == hour:
                        filtered_routes.append(route)

            # Display results
            self._display_direction_table(filtered_routes, origin, destination, "green")

            # Show summary
            self.console.print(
                f"[bold]Found {len(filtered_routes)} routes from {origin} to {destination} at {hour:02d}:00[/bold]"
            )
        except Exception as e:
            self.console.print(
                f"[bold red]Error querying routes:[/bold red] {str(e)}",
                style="red",
            )

    def _get_hebrew_station_name(self, station_name):
        """Convert a station name to Hebrew if it's in English."""
        # Check if the input is already in Hebrew
        if any("\u0590" <= c <= "\u05ff" for c in station_name):
            return station_name

        # Normalize the station name for lookup
        lookup_key = station_name.lower().replace("-", " ").strip()

        # Dictionary of common station translations
        stations = {
            # North
            "nahariya": "נהריה",
            "acre": "עכו",
            "akko": "עכו",
            "haifa hof hakarmel": "חיפה חוף הכרמל",
            "haifa center": "חיפה מרכז",
            "haifa bat galim": "חיפה בת גלים",
            "kiryat haim": "קרית חיים",
            "kiryat motzkin": "קרית מוצקין",
            # Center
            "tel aviv university": "תל אביב - אוניברסיטה",
            "tel aviv merkaz": "תל אביב - מרכז",
            "tel aviv center": "תל אביב - מרכז",
            "tel aviv hashalom": "תל אביב - השלום",
            "tel aviv hahagana": "תל אביב - ההגנה",
            "bnei brak": "בני ברק",
            "petah tikva": "פתח תקווה",
            "herzliya": "הרצליה",
            "raanana west": "רעננה מערב",
            "raanana south": "רעננה דרום",
            "kfar saba": "כפר סבא",
            "netanya": "נתניה",
            # Jerusalem
            "jerusalem navon": "ירושלים - יצחק נבון",
            "jerusalem malha": "ירושלים - מלחה",
            # South
            "lod": "לוד",
            "rehovot": "רחובות",
            "ashdod": "אשדוד",
            "ashkelon": "אשקלון",
            "beer sheva": "באר שבע",
            "beer sheva center": "באר שבע - מרכז",
            "beer sheva north": "באר שבע - צפון",
        }

        # Return the Hebrew name if found, otherwise the original name
        if lookup_key in stations:
            return stations[lookup_key]

        # Warning for missing translations
        self.console.print(
            f"[yellow]Warning:[/yellow] Could not find Hebrew translation for '{station_name}'. Using as-is.",
            style="yellow",
        )
        return station_name
