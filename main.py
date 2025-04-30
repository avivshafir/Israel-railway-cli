import fire
import israelrailapi
from datetime import datetime
import pytz
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
import re
import json


class RailwayCLI:
    """CLI tool for searching train routes in Israel."""

    def __init__(self):
        self.schedule = israelrailapi.TrainSchedule()
        self.console = Console()

    def find_routes_by_hour(self, hour, debug=False):
        """Find train routes between Ra'anana West and Tel Aviv HaShalom at a specific hour.

        Args:
            hour: The hour (0-23) to search for routes
            debug: Whether to print debug information about the route and train objects

        Returns:
            Displays formatted train routes in both directions
        """
        # Convert hour to int and validate
        hour = int(hour)
        if hour < 0 or hour > 23:
            self.console.print(
                f"[bold red]Error:[/bold red] Hour must be between 0 and 23",
                style="red",
            )
            return

        # Get current date in Israel timezone
        israel_tz = pytz.timezone("Asia/Jerusalem")
        current_date = datetime.now(israel_tz).date()

        # Create the date for the search
        search_date = current_date.strftime("%Y-%m-%d")

        # Print date information
        self.console.print(
            Panel(
                f"[bold blue]Searching routes for {search_date} at {hour:02d}:00[/bold blue]"
            )
        )

        # Define the stations with both Hebrew and English names for display
        stations = {
            "raanana_west": {"he": "רעננה מערב", "en": "Ra'anana West"},
            "tel_aviv_hashalom": {"he": "תל אביב - השלום", "en": "Tel Aviv - HaShalom"},
        }

        results = self._query_routes(stations, search_date, hour, debug)
        self._display_results(results, stations, hour)

    def _query_routes(self, stations, search_date, hour, debug=False):
        """Query routes between stations for a specific date and hour."""
        results = {"to_tel_aviv": [], "to_raanana": []}

        # Query routes from Ra'anana West to Tel Aviv HaShalom
        try:
            # Optimize query by including the hour in the request if the API supports it
            to_tel_aviv_routes = self.schedule.query(
                stations["raanana_west"]["he"],
                stations["tel_aviv_hashalom"]["he"],
                search_date,
                f"{hour:02d}:00",  # Include the hour if the API supports it
            )

            # Debug the first route if requested
            if debug and to_tel_aviv_routes:
                self._debug_route_structure(to_tel_aviv_routes[0])

            # Filter routes by the given hour
            for route in to_tel_aviv_routes:
                if hasattr(route, "start_time"):
                    start_time = route.start_time
                    if isinstance(start_time, str):
                        departure_hour = int(start_time.split("T")[1][:2])
                        if departure_hour == hour:
                            results["to_tel_aviv"].append(route)
        except Exception as e:
            self.console.print(
                f"[bold red]Error querying routes from Ra'anana West to Tel Aviv HaShalom:[/bold red] {str(e)}"
            )

        # Query routes from Tel Aviv HaShalom to Ra'anana West
        try:
            to_raanana_routes = self.schedule.query(
                stations["tel_aviv_hashalom"]["he"],
                stations["raanana_west"]["he"],
                search_date,
                f"{hour:02d}:00",  # Include the hour if the API supports it
            )

            # Filter routes by the given hour
            for route in to_raanana_routes:
                if hasattr(route, "start_time"):
                    start_time = route.start_time
                    if isinstance(start_time, str):
                        departure_hour = int(start_time.split("T")[1][:2])
                        if departure_hour == hour:
                            results["to_raanana"].append(route)
        except Exception as e:
            self.console.print(
                f"[bold red]Error querying routes from Tel Aviv HaShalom to Ra'anana West:[/bold red] {str(e)}"
            )

        return results

    def _display_results(self, results, stations, hour):
        """Display train route results in a formatted table."""
        # Display routes from Ra'anana West to Tel Aviv HaShalom
        self._display_direction_table(
            results["to_tel_aviv"],
            stations["raanana_west"]["en"],
            stations["tel_aviv_hashalom"]["en"],
            "green",
        )

        # Display routes from Tel Aviv HaShalom to Ra'anana West
        self._display_direction_table(
            results["to_raanana"],
            stations["tel_aviv_hashalom"]["en"],
            stations["raanana_west"]["en"],
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
            title=title, show_header=True, header_style=f"bold {color}", width=120
        )

        # Add columns
        table.add_column("Departure", style=f"dim {color}")
        table.add_column("Arrival", style=f"dim {color}")
        table.add_column("Duration", style=f"{color}")
        table.add_column("Train #", style=f"dim {color}")
        table.add_column("Transfers", justify="center", style=f"{color}")
        # Removed the Status column
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

            # Add row to table (removed status_info)
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

        # Removed the call to _display_route_stations

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
        except Exception as e:
            # If there's an error, silently skip the station display
            pass

    def _get_train_numbers(self, route):
        """Extract train numbers from the route."""
        if not hasattr(route, "trains") or not route.trains:
            return "N/A"

        try:
            train_nums = []
            for train in route.trains:
                # Based on the debug output, train numbers are in data.trainNumber
                if hasattr(train, "data") and isinstance(train.data, dict):
                    if "trainNumber" in train.data:
                        train_nums.append(str(train.data["trainNumber"]))
                        continue

                    # Fallback to other possible key names if trainNumber isn't found
                    for key in [
                        "Trainno",
                        "trainno",
                        "train_no",
                        "train_number",
                        "number",
                    ]:
                        if key in train.data:
                            train_nums.append(str(train.data[key]))
                            break
                    else:  # No matching key found
                        # Try looking for a key that might contain the train number
                        for key, value in train.data.items():
                            if isinstance(value, str) and re.search(r"\d+", value):
                                if re.search(r"train", key, re.IGNORECASE):
                                    match = re.search(r"\d+", value)
                                    if match:
                                        train_nums.append(match.group(0))
                                        break
                        else:
                            train_nums.append("?")
                else:
                    # Try other possible attribute names directly on the train object
                    if hasattr(train, "train_number"):
                        train_nums.append(str(train.train_number))
                    elif hasattr(train, "number"):
                        train_nums.append(str(train.number))
                    elif hasattr(train, "trainno"):
                        train_nums.append(str(train.trainno))
                    elif hasattr(train, "train_no"):
                        train_nums.append(str(train.train_no))
                    elif hasattr(train, "trainNumber"):
                        train_nums.append(str(train.trainNumber))
                    else:
                        train_nums.append("?")

            # If we couldn't find any train numbers, debug the first train
            if all(num == "?" for num in train_nums) and route.trains:
                self._debug_train_structure(route.trains[0])

            return ", ".join(filter(None, train_nums))  # Filter out any empty strings
        except Exception as e:
            self.console.print(f"Error extracting train numbers: {e}")
            return "?"

    def _debug_train_structure(self, train):
        """Debug method to print train object attributes and their values."""
        self.console.print(
            "[bold yellow]Debugging train object structure:[/bold yellow]"
        )
        attrs = []

        # Get all non-private attributes
        for attr_name in dir(train):
            if attr_name.startswith("_"):
                continue
            try:
                attr_value = getattr(train, attr_name)
                if (
                    isinstance(attr_value, (str, int, float, bool))
                    or attr_value is None
                ):
                    attrs.append((attr_name, attr_value))
                elif isinstance(attr_value, dict):
                    attrs.append(
                        (
                            attr_name,
                            "Dict with keys: " + ", ".join(list(attr_value.keys())),
                        )
                    )
                else:
                    attrs.append((attr_name, f"Type: {type(attr_value).__name__}"))
            except Exception:
                attrs.append((attr_name, "Error accessing value"))

        # Sort attributes by name for easier reading
        attrs.sort(key=lambda x: x[0])

        # Print attributes in a table
        table = Table(
            title="Train Object Structure", show_header=True, header_style="bold yellow"
        )
        table.add_column("Attribute", style="dim")
        table.add_column("Value/Type", style="green")

        for attr_name, attr_value in attrs:
            table.add_row(attr_name, str(attr_value))

        self.console.print(table)

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

        try:
            # For each pair of consecutive trains, the transfer is where one ends and the next begins
            transfer_details = []

            for i in range(len(route.trains) - 1):
                current_train = route.trains[i]
                next_train = route.trains[i + 1]

                # Using the train attributes directly now that we know what they are
                if hasattr(current_train, "dst") and hasattr(next_train, "src"):
                    # The transfer station is the destination of the current train
                    transfer_station_code = current_train.dst
                    transfer_station = self._get_station_name(
                        str(transfer_station_code), hebrew=False
                    )

                    # Get the train numbers
                    current_train_num = self._get_single_train_number(current_train)
                    next_train_num = self._get_single_train_number(next_train)

                    # Get the arrival time at the transfer station and the departure time of next train
                    if hasattr(current_train, "arrival") and hasattr(
                        next_train, "departure"
                    ):
                        arrival_time = current_train.arrival
                        departure_time = next_train.departure

                        # Format the times
                        arrival_formatted = self._format_time(arrival_time)
                        departure_formatted = self._format_time(departure_time)

                        # Calculate wait time
                        wait_minutes = self._calculate_wait_time(
                            arrival_time, departure_time
                        )

                        # Platform information if available
                        arrival_platform = (
                            f" (platform {current_train.dst_platform})"
                            if hasattr(current_train, "dst_platform")
                            and current_train.dst_platform
                            else ""
                        )
                        departure_platform = (
                            f" (platform {next_train.platform})"
                            if hasattr(next_train, "platform") and next_train.platform
                            else ""
                        )

                        transfer_details.append(
                            f"{transfer_station}: {current_train_num} → {next_train_num}\n"
                            + f"  Arrive: {arrival_formatted}{arrival_platform}\n"
                            + f"  Depart: {departure_formatted}{departure_platform}\n"
                            + f"  Wait: {wait_minutes}m"
                        )
                    else:
                        # Fallback if no time information is available
                        transfer_details.append(
                            f"{transfer_station}: {current_train_num} → {next_train_num}"
                        )
                else:
                    # Fallback if no station information is available
                    transfer_details.append("Change trains")

            return "\n\n".join(transfer_details)
        except Exception as e:
            self.console.print(f"Error extracting transfer details: {e}")
            return "Change trains (details unavailable)"

    def _get_single_train_number(self, train):
        """Extract a single train number from a train object."""
        try:
            if (
                hasattr(train, "data")
                and isinstance(train.data, dict)
                and "trainNumber" in train.data
            ):
                return f"Train #{train.data['trainNumber']}"

            # Try other possible locations
            if hasattr(train, "train_number"):
                return f"Train #{train.train_number}"
            elif hasattr(train, "trainNumber"):
                return f"Train #{train.trainNumber}"

            return "Unknown Train"
        except Exception:
            return "Unknown Train"

    def _format_time(self, time_str):
        """Format ISO time string to HH:MM."""
        if not time_str or not isinstance(time_str, str):
            return "N/A"

        try:
            # Extract time part (HH:MM:SS) from ISO format (YYYY-MM-DDTHH:MM:SS)
            time_part = time_str.split("T")[1][:5]  # Extract HH:MM
            return time_part
        except (IndexError, AttributeError):
            return "N/A"

    def _calculate_duration(self, start_time, end_time):
        """Calculate and format journey duration in minutes."""
        if (
            not start_time
            or not end_time
            or not isinstance(start_time, str)
            or not isinstance(end_time, str)
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
                hours = int(duration_minutes // 60)
                mins = int(duration_minutes % 60)
                return f"{hours}h {mins}m"
            else:
                return f"{int(duration_minutes)}m"
        except (ValueError, TypeError):
            return "N/A"

    def _calculate_wait_time(self, arrival_time, departure_time):
        """Calculate wait time between arrival and departure in minutes."""
        if (
            not arrival_time
            or not departure_time
            or not isinstance(arrival_time, str)
            or not isinstance(departure_time, str)
        ):
            return 0

        try:
            # Parse ISO datetime strings
            arrival = datetime.fromisoformat(arrival_time.replace("Z", "+00:00"))
            departure = datetime.fromisoformat(departure_time.replace("Z", "+00:00"))

            # Calculate wait time in minutes
            wait_minutes = (departure - arrival).total_seconds() / 60

            return max(0, int(wait_minutes))
        except (ValueError, TypeError) as e:
            self.console.print(f"Error calculating wait time: {e}")
            return 0

    def _debug_route_structure(self, route):
        """Debug method to print route object attributes and their values."""
        self.console.print(
            "[bold magenta]Debugging route object structure:[/bold magenta]"
        )
        attrs = []

        # Get all non-private attributes
        for attr_name in dir(route):
            if attr_name.startswith("_"):
                continue
            try:
                attr_value = getattr(route, attr_name)
                if (
                    isinstance(attr_value, (str, int, float, bool))
                    or attr_value is None
                ):
                    attrs.append((attr_name, attr_value))
                elif isinstance(attr_value, dict):
                    attrs.append(
                        (
                            attr_name,
                            "Dict with keys: " + ", ".join(list(attr_value.keys())),
                        )
                    )
                elif isinstance(attr_value, list):
                    if attr_name == "trains" and attr_value:
                        attrs.append((attr_name, f"List with {len(attr_value)} trains"))
                        # Debug the first train
                        if attr_value:
                            self._debug_train_structure(attr_value[0])
                    else:
                        attrs.append((attr_name, f"List with {len(attr_value)} items"))
                else:
                    attrs.append((attr_name, f"Type: {type(attr_value).__name__}"))
            except Exception:
                attrs.append((attr_name, "Error accessing value"))

        # Sort attributes by name for easier reading
        attrs.sort(key=lambda x: x[0])

        # Print attributes in a table
        table = Table(
            title="Route Object Structure",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Attribute", style="dim")
        table.add_column("Value/Type", style="green")

        for attr_name, attr_value in attrs:
            table.add_row(attr_name, str(attr_value))

        self.console.print(table)

    def find_routes(self, origin, destination, hour, date=None, debug=False):
        """Find train routes between any two stations at a specific hour.

        Args:
            origin: The origin station name (in Hebrew or English)
            destination: The destination station name (in Hebrew or English)
            hour: The hour (0-23) to search for routes
            date: Optional date in YYYY-MM-DD format. If not provided, uses current date.
            debug: Whether to print debug information about the route and train objects

        Returns:
            Displays formatted train routes
        """
        # Convert hour to int and validate
        hour = int(hour)
        if hour < 0 or hour > 23:
            self.console.print(
                f"[bold red]Error:[/bold red] Hour must be between 0 and 23",
                style="red",
            )
            return

        # Get current date in Israel timezone if not provided
        if date is None:
            israel_tz = pytz.timezone("Asia/Jerusalem")
            current_date = datetime.now(israel_tz).date()
            search_date = current_date.strftime("%Y-%m-%d")
        else:
            # Validate and use provided date
            try:
                # Check if date is in YYYY-MM-DD format
                if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
                    raise ValueError("Date must be in YYYY-MM-DD format")
                search_date = date
            except ValueError as e:
                self.console.print(
                    f"[bold red]Error:[/bold red] {str(e)}",
                    style="red",
                )
                return

        # Print search information
        self.console.print(
            Panel(
                f"[bold blue]Searching routes from {origin} to {destination} for {search_date} at {hour:02d}:00[/bold blue]"
            )
        )

        # Try to detect if the input is in Hebrew or English and convert if needed
        origin_he = self._get_hebrew_station_name(origin)
        destination_he = self._get_hebrew_station_name(destination)

        # Query the routes
        try:
            routes = self.schedule.query(
                origin_he,
                destination_he,
                search_date,
                f"{hour:02d}:00",
            )

            # Debug the first route if requested
            if debug and routes:
                self._debug_route_structure(routes[0])

            # Filter routes by the given hour
            filtered_routes = []
            for route in routes:
                if hasattr(route, "start_time"):
                    start_time = route.start_time
                    if isinstance(start_time, str):
                        departure_hour = int(start_time.split("T")[1][:2])
                        if departure_hour == hour:
                            filtered_routes.append(route)

            # Display the routes
            self._display_direction_table(
                filtered_routes,
                origin,
                destination,
                "green",
            )

            # Report the number of routes found
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
        # Common station translations for the Israel Railways
        station_translations = {
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

        # Check if the input is already in Hebrew
        if any("\u0590" <= c <= "\u05ff" for c in station_name):
            return station_name

        # Try to find a translation
        station_key = station_name.lower().replace("-", " ").strip()
        if station_key in station_translations:
            return station_translations[station_key]

        # If no translation found, return the original input
        # This allows the API to try with the original input
        self.console.print(
            f"[yellow]Warning:[/yellow] Could not find Hebrew translation for '{station_name}'. Using as-is.",
            style="yellow",
        )
        return station_name


if __name__ == "__main__":
    fire.Fire(RailwayCLI)
