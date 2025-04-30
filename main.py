import fire
import israelrailapi
from datetime import datetime
import pytz
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text


class RailwayCLI:
    """CLI tool for searching train routes in Israel."""

    def __init__(self):
        self.schedule = israelrailapi.TrainSchedule()
        self.console = Console()

    def find_routes_by_hour(self, hour):
        """Find train routes between Ra'anana West and Tel Aviv HaShalom at a specific hour.

        Args:
            hour: The hour (0-23) to search for routes

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

        results = self._query_routes(stations, search_date, hour)
        self._display_results(results, stations, hour)

    def _query_routes(self, stations, search_date, hour):
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

        # Create a table for this direction
        title = f"[bold {color}]Routes from {origin} to {destination}[/bold {color}]"
        table = Table(title=title, show_header=True, header_style=f"bold {color}")

        # Add columns
        table.add_column("Departure", style=f"dim {color}")
        table.add_column("Arrival", style=f"dim {color}")
        table.add_column("Duration", style=f"{color}")
        table.add_column("Transfers", justify="center", style=f"{color}")
        table.add_column("Transfer Details", style=f"italic {color}")

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

            # Get transfer details if there's a transfer
            transfer_details = (
                self._get_transfer_details(route) if transfers > 0 else "-"
            )

            # Add row to table
            table.add_row(
                start_time, end_time, duration, transfers_text, transfer_details
            )

        # Print the table
        self.console.print(Panel(table, border_style=color))

    def _get_transfer_details(self, route):
        """Extract transfer details from a route with transfers."""
        if not hasattr(route, "trains") or len(route.trains) <= 1:
            return "-"

        try:
            # For each pair of consecutive trains, the transfer is where one ends and the next begins
            transfer_details = []

            for i in range(len(route.trains) - 1):
                # Find the destination station of the current train
                # (which is the transfer station)
                current_train = route.trains[i]
                next_train = route.trains[i + 1]

                # Extract transfer station name - assuming the last station of the first train
                # is where the transfer happens
                if hasattr(current_train, "__str__"):
                    train_str = str(current_train)
                    # Parse the string representation to extract destination
                    if " to " in train_str:
                        transfer_station = train_str.split(" to ")[1].split(" (")[0]
                        # Get transfer time
                        transfer_time = "?"
                        if hasattr(current_train, "destination_time") and hasattr(
                            next_train, "origin_time"
                        ):
                            dest_time = self._format_time(
                                current_train.destination_time
                            )
                            origin_time = self._format_time(next_train.origin_time)
                            wait_minutes = self._calculate_wait_time(
                                current_train.destination_time, next_train.origin_time
                            )
                            transfer_time = (
                                f"{dest_time} → {origin_time} ({wait_minutes}m wait)"
                            )

                        transfer_details.append(
                            f"{transfer_station} at {transfer_time}"
                        )
                    else:
                        # If we can't parse the string format, try a different approach
                        transfer_details.append(f"Change trains")
                else:
                    # Fallback if we can't extract detailed information
                    transfer_details.append(f"Change trains")

            return "\n".join(transfer_details)

        except Exception as e:
            # If anything goes wrong, provide a simple fallback
            return "Change trains"

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

    def _calculate_wait_time(self, end_time, start_time):
        """Calculate wait time between arrival and departure in minutes."""
        if (
            not start_time
            or not end_time
            or not isinstance(start_time, str)
            or not isinstance(end_time, str)
        ):
            return "?"

        try:
            # Parse ISO datetime strings
            end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))

            # Calculate wait time in minutes
            wait_minutes = (start - end).total_seconds() / 60

            return int(wait_minutes)
        except (ValueError, TypeError):
            return "?"


if __name__ == "__main__":
    fire.Fire(RailwayCLI)
