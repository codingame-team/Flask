# coding: utf-8
import os
import locale
from math import radians, sin, cos, sqrt, atan2, pi
from typing import List, Tuple
from pytz import timezone
from gpxpy import parse
from gpxpy.gpx import GPX, MovingData
from common import get_strava_path, resource_path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import matplotlib as mpl


class PositionGPS:
	def __init__(self, latitude, longitude, lieu_dit):
		self.latitude = float(latitude)
		self.longitude = float(longitude)
		self.lieu_dit = lieu_dit

	def calculate_distance_vol_oiseau(self, other) -> float:
		"""Calculate great-circle distance between two points using Haversine formula."""
		R = 6371.0  # Earth radius in km
		lat1, lon1 = map(radians, (self.latitude, self.longitude))
		lat2, lon2 = map(radians, (other.latitude, other.longitude))
		a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
		return 2 * R * atan2(sqrt(a), sqrt(1 - a))


def decathlon_message(filename, day, hour, elapsed_time, distance, moving_data) -> str:
	elapsed_hours, elapsed_minutes = divmod(elapsed_time / 60, 60)
	max_speed_kmh = moving_data.max_speed * 3600 / 1000
	average_speed_kmh = moving_data.moving_distance / (1000 * moving_data.moving_time / 3600)
	activity_label: str = filename.split('.')[0]
	return (f"Le {day} à {hour}, vous avez débuté une activité sportive intitulée \"{activity_label}\" et parcouru une distance "
			f"de {distance:.1f} km pour une durée de {int(elapsed_hours)}h{round(elapsed_minutes)}mn, avec une vitesse moyenne de {average_speed_kmh:.2f} km/h et un vitesse maximale de {max_speed_kmh:.2f} km/h.")


def get_activities() -> list[tuple]:
	gpx_strava_path = get_strava_path()
	os.makedirs(gpx_strava_path, exist_ok=True)
	activities: list = []
	for filename in sorted(os.listdir(gpx_strava_path)):
		if filename.endswith('.gpx'):
			# print("-" * 80)
			with open(resource_path(f'{gpx_strava_path}/{filename}'), 'r') as gpx_file:
				gpx: GPX = parse(gpx_file)
				moving_data: MovingData = gpx.get_moving_data()
				locale.setlocale(locale.LC_TIME, 'fr_FR')
				start_time = gpx.get_time_bounds().start_time.astimezone(timezone('Europe/Paris'))
				end_time = gpx.get_time_bounds().end_time.astimezone(timezone('Europe/Paris'))
				day, hour = start_time.strftime('%A %d %B %Y'), start_time.strftime('%Hh%M')
				elapsed_time = gpx.get_duration()
				distance3d = gpx.length_3d() / 1000
				max_speed_kmh = moving_data.max_speed * 3600 / 1000
				average_speed_kmh = moving_data.moving_distance / (1000 * moving_data.moving_time / 3600)
				activity_label: str = filename.split('.')[0]
				elapsed_hours, elapsed_minutes = divmod(elapsed_time / 60, 60)
				duration: str = f'{int(elapsed_hours)}h {round(elapsed_minutes)}\''
				# activities.append((day, hour, distance3d, duration, average_speed_kmh, max_speed_kmh, activity_label))
				activities.append((start_time, distance3d, elapsed_time, average_speed_kmh, max_speed_kmh, activity_label))
	return activities


def create_dataframe(activities: List[Tuple]) -> pd.DataFrame:
	data = {'Date': [], 'Distance': [], 'Duration': [], 'Average_Speed': [], 'Max_Speed': [], 'Activity_Label': []}

	for activity_date, distance3d, duration, average_speed_kmh, max_speed_kmh, activity_label in activities:
		data['Date'].append(activity_date)
		data['Distance'].append(distance3d)
		data['Duration'].append(duration / 3600)  # Convert seconds to hours
		data['Average_Speed'].append(average_speed_kmh)
		data['Max_Speed'].append(max_speed_kmh)
		data['Activity_Label'].append(activity_label)

	df = pd.DataFrame(data)
	df['Date'] = pd.to_datetime(df['Date'])
	return df.sort_values(by='Date', ascending=True).reset_index(drop=True)


def create_single_plot(df: pd.DataFrame, metric: str, color: str, ylabel: str) -> None:
	fig, ax = plt.subplots(figsize=(12, 6))

	# Plot line connecting points
	ax.plot(df['Date'], df[metric], color=color, linewidth=1, alpha=0.5, zorder=1)

	# Plot points
	scatter = ax.scatter(df['Date'], df[metric], color=color, s=50, zorder=2, label=metric.replace('_', ' '))

	# Add tooltips
	def on_hover(event):
		if event.inaxes == ax:
			cont, ind = scatter.contains(event)
			if cont:
				point_index = ind["ind"][0]
				tooltip_text = (f'Date: {df["Date"].iloc[point_index].strftime("%Y-%m-%d")}\n'
								f'{metric.replace("_", " ")}: {df[metric].iloc[point_index]:.2f}\n'
								f'Activity: {df["Activity_Label"].iloc[point_index]}')

				# Remove existing tooltips
				for child in ax.get_children():
					if isinstance(child, mpl.text.Annotation):
						child.remove()

				ax.annotate(tooltip_text, xy=(df['Date'].iloc[point_index], df[metric].iloc[point_index]), xytext=(10, 10), textcoords='offset points', bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5), arrowprops=dict(arrowstyle='->'))
				plt.draw()

	fig.canvas.mpl_connect('motion_notify_event', on_hover)

	# Customize plot
	plt.title(f'{metric.replace("_", " ")} Over Time', fontsize=14, pad=20)
	plt.xlabel('Date', fontsize=12)
	plt.ylabel(ylabel, fontsize=12)
	plt.legend()
	plt.grid(True, alpha=0.3)
	plt.xticks(rotation=45)

	# Save plot
	plt.tight_layout()
	plt.savefig(f'{metric.lower()}_trend.png', dpi=300, bbox_inches='tight')

	# Return figure for later use
	return fig


def decathlon_main():
	# Set style
	sns.set_style("whitegrid")

	# Define plot configurations
	plot_configs = [{'metric': 'Distance', 'color': 'blue', 'ylabel': 'Distance (km)'},
					{'metric': 'Duration', 'color': 'green', 'ylabel': 'Duration (hours)'},
					{'metric': 'Average_Speed', 'color': 'red', 'ylabel': 'Average Speed (km/h)'},
					{'metric': 'Max_Speed', 'color': 'purple', 'ylabel': 'Max Speed (km/h)'}]

	# Create DataFrame
	df = create_dataframe(activities=get_activities())

	# Create individual plots and store figures
	figures = []
	for config in plot_configs:
		fig = create_single_plot(df, metric=config['metric'], color=config['color'], ylabel=config['ylabel'])
		figures.append(fig)

	# Print summary statistics
	print("\nActivity Summary Statistics:")
	print(df.describe().round(2))

	# Show all plots
	plt.show()

	return df


if __name__ == '__main__':
	# covid_main()
	decathlon_main()
