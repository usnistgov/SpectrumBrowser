package gov.nist.spectrumbrowser.client;

import java.util.Date;
import java.util.HashSet;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.core.client.GWT;
import com.google.gwt.core.client.Scheduler;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.i18n.client.DateTimeFormat;
import com.google.gwt.i18n.client.DateTimeFormat.PredefinedFormat;
import com.google.gwt.i18n.client.NumberFormat;
import com.google.gwt.i18n.client.TimeZone;
import com.google.gwt.i18n.client.constants.TimeZoneConstants;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.maps.client.InfoWindow;
import com.google.gwt.maps.client.InfoWindowContent;
import com.google.gwt.maps.client.MapWidget;
import com.google.gwt.maps.client.Maps;
import com.google.gwt.maps.client.event.MarkerClickHandler;
import com.google.gwt.maps.client.geom.LatLng;
import com.google.gwt.maps.client.geom.Point;
import com.google.gwt.maps.client.geom.Size;
import com.google.gwt.maps.client.overlay.Icon;
import com.google.gwt.maps.client.overlay.Marker;
import com.google.gwt.maps.client.overlay.MarkerOptions;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.DialogBox;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.MenuBar;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.google.gwt.user.datepicker.client.DateBox;
import com.smartgwt.client.widgets.events.ClickEvent;
import com.smartgwt.client.widgets.toolbar.ToolStripButton;

public class SpectrumBrowserShowDatasets {
	public static final String END_LABEL = "Select Data Set";

	public static final String LABEL = END_LABEL+ " >>";
	
	private static final long SECONDS_PER_DAY = 24 * 60 * 60;

	SpectrumBrowser spectrumBrowser;
	VerticalPanel verticalPanel;
	MapWidget map;
	String selectedMarkerId;
	int ndays;
	HashSet<SensorMarker> sensorMarkers = new HashSet<SensorMarker>();
	SensorMarker selectedMarker;
	Grid selectionGrid;
	DateBox startDateCalendar;
	NameValueBox maxFreqLabel;
	NameValueBox minFreqLabel;
	NameValueBox readingsCountLabel;
	NameValueBox maxOccupancyLabel;
	NameValueBox minOccupancyLabel;
	NameValueBox meanOccupancyLabel;
	NameValueBox availableDayCountField;
	NameValueBox dayCountField;
	HorizontalPanel selectionGridPanel;
	private TextInputBox userDayCountField;
	private Button showStatisticsButton;

	static Logger logger = Logger.getLogger("SpectrumBrowser");

	abstract class SensorMarkerRunnable implements Runnable {
		GoogleTimeZoneClient client;

		public SensorMarkerRunnable(GoogleTimeZoneClient client) {
			this.client = client;
		}
	}

	class SensorMarker extends Marker {
		private JSONObject locationMessageJsonObject;
		private String timeZoneId;

		private String measurementType;

		private long tInstall;
		private long tInstallLocalTime;
		private String tInstallLocalTimeTzName;
		
		private long tStart;
		private long tStartLocalTime;
		private String tStartLocalTimeTzName;
		
		private long tSelectedStartTime;

		private boolean selected;
		private long tStartReadings;
		private long tEndReadings;
		private long tEndReadingsLocalTime;
		private String tEndReadingsLocalTimeTzName;
		
		private long utcOffset;

		private double maxOccupancy;
		private double minOccupancy;
		private double meanOccupancy;
		private double dataSetMaxOccupancy;
		private double dataSetMinOccupancy;
		private double dataSetMeanOccupancy;
		private long minFreq;
		private long dataSetMinFreq;
		private long maxFreq;
		private long dataSetMaxFreq;
		private long readingsCount;
		private long dataSetReadingsCount;
		private int availableDayCount; // Max number of days available.
		private boolean firstUpdate = true;
		private int dayCount;
		private InfoWindowContent iwc;

		public void setSelected(boolean flag) {
			selected = flag;
			if (!flag) {
				String iconPath = SpectrumBrowser.getBaseUrl()
						+ "../icons/mm_20_red.png";
				setImage(iconPath);
				selectedMarker = null;
			} else {
				String iconPath = SpectrumBrowser.getBaseUrl()
						+ "../icons/mm_20_yellow.png";
				setImage(iconPath);
				selectedMarker = this;
			}
		}

		public boolean isSelected() {
			return selected;
		}

		private void updateDataSummary(long startTime, long endTime) {
			String sessionId = spectrumBrowser.getSessionId();
			String sensorId = getId();
			String locationMessageId = locationMessageJsonObject.get("_id").isObject()
					.get("$oid").isString().stringValue();

			spectrumBrowser.getSpectrumBrowserService().getDataSummary(
					sessionId, sensorId, locationMessageId,
					startTime, endTime, new SpectrumBrowserCallback<String>() {
						@Override
						public void onSuccess(String text) {
							try {
								// Note that POST replies are returned
								// asynchronously
								logger.fine(text);
								JSONObject jsonObj = (JSONObject) JSONParser
										.parseLenient(text);
								readingsCount = (long) jsonObj
										.get("readingsCount").isNumber()
										.doubleValue();
								if (readingsCount == 0) {
									logger.finer("ReadingsCount is 0");
									return;
								}

								measurementType = jsonObj
										.get("measurementType").isString()
										.stringValue();
								logger.finer(measurementType);

								tStartReadings = (long) jsonObj
										.get("tStartReadings").isNumber()
										.doubleValue();
								logger.finer("tStartReadings " + tStartReadings);

								tEndReadings = (long) jsonObj
										.get("tEndReadings").isNumber()
										.doubleValue();
								
								minFreq = (long) jsonObj.get("minFreq")
										.isNumber().doubleValue() / 1000000;
								maxFreq = (long) jsonObj.get("maxFreq")
										.isNumber().doubleValue() / 1000000;
								maxOccupancy = jsonObj.get("maxOccupancy")
										.isNumber().doubleValue();
								minOccupancy = jsonObj.get("minOccupancy")
										.isNumber().doubleValue();
								meanOccupancy = jsonObj.get("meanOccupancy")
										.isNumber().doubleValue();
								logger.finer("meanOccupancy" + meanOccupancy);
								
								

								
								// For the first update, we translate UTC
								// readings
								// to the local time zone. We use google Time
								// API
								// for this.
								if (firstUpdate) {
									firstUpdate = false;

									availableDayCount = (int) ((tEndReadings - tStartReadings) / SECONDS_PER_DAY);
									logger.finer("availableDayCount " + availableDayCount);
									dataSetReadingsCount = readingsCount;
									dataSetMaxOccupancy = maxOccupancy;
									dataSetMinOccupancy = minOccupancy;
									dataSetMeanOccupancy = meanOccupancy;
									dataSetMinFreq = minFreq;
									dataSetMaxFreq = maxFreq;
									tStartLocalTime = (long) jsonObj
											.get("tStartLocalTime").isNumber()
											.doubleValue();
									tStartLocalTimeTzName = jsonObj.get("tStartLocalTimeTzName").isString().stringValue();
									tSelectedStartTime = tStartLocalTime;
									logger.finer("tStartLocalTime " + tStartLocalTime);
									tEndReadingsLocalTime = (long) jsonObj
											.get("tEndReadingsLocalTime")
											.isNumber().doubleValue();
									tEndReadingsLocalTimeTzName = jsonObj.get("tEndReadingsLocalTimeTzName").isString().stringValue();
									logger.finer("tEndReadings " + tEndReadings);
									
								} else {
									// Otherwise, immediately show the updates
									// of
									// summary data.
									showSummary();
								}
							} catch (Throwable ex) {
								logger.log(Level.SEVERE,"Error Parsing returned data ",ex);
								spectrumBrowser
										.displayError("Error parsing returned data!");
							}
							iwc = new InfoWindowContent(getInfo());
							

						}

						@Override
						public void onFailure(Throwable throwable) {
							logger.log(Level.SEVERE,
									"Error occured in processing request",
									throwable);
							spectrumBrowser
									.displayError("Error in contacting server. Try later");
							return;

						}

					});
		}

		public SensorMarker(LatLng point, MarkerOptions markerOptions,
				JSONObject jsonObject) {

			super(point, markerOptions);
			try {
				this.locationMessageJsonObject = jsonObject;
				// Extract the data values.
				tInstall = (long) jsonObject.get("tInstall").isNumber()
						.doubleValue();
				tInstallLocalTime = (long) jsonObject.get("tInstallLocalTime")
						.isNumber().doubleValue();
				tInstallLocalTimeTzName = jsonObject.get("tInstallLocalTimeTzName").isString().stringValue();
				tStart = (long) jsonObject.get("t").isNumber().doubleValue();
				tStartLocalTime = (long) jsonObject.get("tStartLocalTime").isNumber()
						.doubleValue();
				timeZoneId = jsonObject.get("timeZone").isString().stringValue();
				updateDataSummary(-1, -1);
				startDateCalendar
						.addValueChangeHandler(new ValueChangeHandler<Date>() {

							@Override
							public void onValueChange(
									ValueChangeEvent<Date> event) {
								logger.finer("Calendar valueChanged "
										+ event.getValue().getTime()
										+ " tStartLocalTime " + tStartLocalTime
										* 1000 + " tEndLocalTime "
										+ tEndReadingsLocalTime * 1000);
								Date eventDate = event.getValue();
								if (eventDate.getTime() <= tStartLocalTime * 1000) {
									startDateCalendar.getDatePicker().setValue(
											new Date(tStartLocalTime * 1000));
									startDateCalendar
											.getDatePicker()
											.setCurrentMonth(
													new Date(
															tStartLocalTime * 1000));
								} else if (eventDate.getTime() >= tEndReadingsLocalTime * 1000) {
									startDateCalendar
											.getDatePicker()
											.setValue(
													new Date(
															tEndReadingsLocalTime * 1000));
									startDateCalendar
											.getDatePicker()
											.setCurrentMonth(
													new Date(
															tEndReadingsLocalTime * 1000));

								} else {
									logger.finer("Date in acceptable range");
									tSelectedStartTime = eventDate.getTime() / 1000;
									startDateCalendar.getDatePicker().setValue(
											eventDate);
									startDateCalendar.getDatePicker().setCurrentMonth(eventDate);

									if (userDayCountField.isNonNegative()) {
										String dayCountString = userDayCountField
												.getValue();
										dayCount = Integer
												.parseInt(dayCountString);
										logger.finest("dayCount = " + dayCount);

										long endTime = tSelectedStartTime
												+ dayCount * SECONDS_PER_DAY;
										updateDataSummary(tSelectedStartTime,
												endTime);
									} else {
										updateDataSummary(tSelectedStartTime,
												-1);
									}

								}

							}
						});

			} catch (Exception ex) {
				logger.log(Level.SEVERE,
						"Error sending request to timezone server", ex);
			}
		}

		public double getAlt() {
			return locationMessageJsonObject.get("Alt").isNumber().doubleValue();
		}

		public String getInfo() {

			return "<b color=\"red\" > Click on marker again to select sensor. </b>"
					+ "<div align=\"left\", height=\"300px\">" + "<br/>sensor ID = "
					+ getId()
					+ "<br/>Lat = "
					+ getLatLng().getLatitude()
					+ " Long = "
					+ getLatLng().getLongitude()
					+ " Alt = "
					+ getAlt()
					+ "Ft."
					+ "<br/>mType = "
					+ measurementType
					+ "<br/>tInstall = "
					+ getTinstallLocalTimeAsString()
					+ " tStart = "
					+ getTstartLocalTimeAsString()
					+ " tEnd = "
					+ getTendReadingsLocalTimeAsString()
					+ "<br/>fStart = "
					+ dataSetMinFreq
					+ "MHz"
					+ " fStop = "
					+ dataSetMaxFreq
					+ "MHz"
					+ "<br/>max Occupancy = "
					+ formatToPrecision(2, dataSetMaxOccupancy * 100)
					+ "%"
					+ " min Occupancy = "
					+ formatToPrecision(2, dataSetMinOccupancy * 100)
					+ "%"
					+ " mean Occupancy = "
					+ formatToPrecision(2, dataSetMeanOccupancy * 100)
					+ "%"
					+ "<br/>Acquisition Count = " + dataSetReadingsCount + "<br/></div>";
		}

		public String getTstartLocalTimeAsString() {
			DateTimeFormat formatter = DateTimeFormat
					.getFormat("yyyy-MM-dd HH:mm:ss");
			return formatter.format(new Date(tStartLocalTime * 1000)) + " "
					+ tStartLocalTimeTzName;
		}

		public String getTinstallLocalTimeAsString() {
			DateTimeFormat formatter = DateTimeFormat
					.getFormat("yyyy-MM-dd HH:mm:ss");
			return formatter.format(new Date(tInstallLocalTime * 1000)) + " "
					+ tInstallLocalTimeTzName;
		}

		public String getTendReadingsLocalTimeAsString() {
			DateTimeFormat formatter = DateTimeFormat
					.getFormat("yyyy-MM-dd HH:mm:ss");
			return formatter.format(new Date(tEndReadingsLocalTime * 1000))
					+ " " + tEndReadingsLocalTimeTzName;
		}

		public String getId() {
			return locationMessageJsonObject.get("sensorID").isString().stringValue();

		}

		double getMaxOccupancy() {
			return maxOccupancy;
		}

		double getMinOccupancy() {
			return minOccupancy;
		}

		double getMeanOccupancy() {
			return meanOccupancy;
		}

		long getMinFreq() {
			return minFreq;
		}

		long getMaxFreq() {
			return maxFreq;
		}

		long getReadingsCount() {
			return readingsCount;
		}

		void showSummary() {
			maxOccupancyLabel.setValue(formatToPrecision(2, maxOccupancy * 100)
					+ "%");
			minOccupancyLabel.setValue(formatToPrecision(2, minOccupancy * 100)
					+ "%");
			meanOccupancyLabel.setValue(formatToPrecision(2,
					meanOccupancy * 100) + "%");
			readingsCountLabel.setValue(Long.toString(readingsCount));
			dayCountField.setValue(Long.toString(availableDayCount));
			startDateCalendar.setValue(new Date(tSelectedStartTime * 1000));
			minFreqLabel.setValue(Long.toString(minFreq));
			maxFreqLabel.setValue(Long.toString(maxFreq));
			userDayCountField.setEnabled(true);
			startDateCalendar.setEnabled(true);
			final int maxDayCount = (int) ((tEndReadingsLocalTime - tSelectedStartTime) / SECONDS_PER_DAY);

			final int allowableDayCount = measurementType.equals("FFT-Power") ? Math
					.min(14, maxDayCount) : Math.min(30, maxDayCount);
			if (dayCount <= 0
					|| !userDayCountField.isInteger()
					|| Integer.parseInt(userDayCountField.getValue()) > allowableDayCount) {
				dayCount = allowableDayCount;
				userDayCountField.setValue(Integer.toString(dayCount));
			}
			showStatisticsButton.setEnabled(true);
			userDayCountField.addValueChangedHandler(new Runnable() {

				@Override
				public void run() {
					if (userDayCountField.isNonNegative()) {
						int userSelectedDayCount = Integer
								.parseInt(userDayCountField.getValue());
						long selectedEndTime = tSelectedStartTime
								+ userSelectedDayCount * SECONDS_PER_DAY;
						updateDataSummary(tSelectedStartTime, selectedEndTime);
					} else {
						updateDataSummary(tSelectedStartTime, -1);
					}
				}
			}, allowableDayCount);
		}

		public long getSelectedStartTime() {
			return this.tSelectedStartTime;
		}

		public int getDayCount() {
			return this.dayCount;
		}

		public InfoWindowContent getInfoWindowContent() {
			return iwc;
		}
		

	}

	public SpectrumBrowserShowDatasets(SpectrumBrowser spectrumBrowser,
			VerticalPanel verticalPanel) {
		this.spectrumBrowser = spectrumBrowser;
		this.verticalPanel = verticalPanel;
		// Google API key goes here.
		Maps.loadMapsApi(SpectrumBrowser.API_KEY, "2", false, new Runnable() {
			public void run() {
				buildUi();
			}
		});

	}

	public String formatToPrecision(int precision, double value) {
		String format = "00.";
		for (int i = 0; i < precision; i++) {
			format += "0";
		}
		return NumberFormat.getFormat(format).format(value);
	}

	public void setSummaryUndefined() {
		maxFreqLabel.setValue("NaN");
		minFreqLabel.setValue("NaN");
		readingsCountLabel.setValue("NaN");
		maxOccupancyLabel.setValue("NaN");
		minOccupancyLabel.setValue("NaN");
		meanOccupancyLabel.setValue("NaN");
		dayCountField.setValue("NaN");
		startDateCalendar.setEnabled(false);
		userDayCountField.setEnabled(false);
		showStatisticsButton.setEnabled(false);

	}

	public double getSelectedLatitude() {
		if (selectedMarker != null) {
			return selectedMarker.getLatLng().getLatitude();
		} else
			return (double) -100;
	}

	public double getSelectedLongitude() {
		return selectedMarker != null ? selectedMarker.getLatLng()
				.getLongitude() : -100;
	}

	public void buildUi() {
		try {

			verticalPanel.clear();
			MenuBar menuBar = new MenuBar();
			SafeHtmlBuilder safeHtml = new SafeHtmlBuilder();
			menuBar.addItem(safeHtml.appendEscaped("Log Off").toSafeHtml(),
					new Scheduler.ScheduledCommand() {

						@Override
						public void execute() {
							spectrumBrowser.logoff();

						}
					});

			menuBar.addItem(
					new SafeHtmlBuilder().appendEscaped(
							"Select by Frequency Range").toSafeHtml(),
					new Scheduler.ScheduledCommand() {

						@Override
						public void execute() {
							DialogBox dialogBox = new DialogBox();
							dialogBox.setText("Help text");

						}
					});

			menuBar.addItem(new SafeHtmlBuilder().appendEscaped("Help")
					.toSafeHtml(), new Scheduler.ScheduledCommand() {

				@Override
				public void execute() {

				}
			});

			menuBar.addItem(new SafeHtmlBuilder().appendEscaped("About")
					.toSafeHtml(), new Scheduler.ScheduledCommand() {

				@Override
				public void execute() {
					// TODO

				}
			});

			verticalPanel
					.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);

			verticalPanel.add(menuBar);

			HTML html = new HTML("<h1>Select sensor</h1>", true);
			verticalPanel.add(html);

			selectionGrid = new Grid(2, 5);
			selectionGrid.setVisible(true);
			selectionGrid.setStyleName("selectionGrid");

			showStatisticsButton = new Button("Show Statistics");

			dayCountField = new NameValueBox("Avail Length (days)", "NaN");
			userDayCountField = new TextInputBox("Run Length (days)", "Specify");
			startDateCalendar = new DateBox();
			minFreqLabel = new NameValueBox("Min Freq (MHz)", "NaN");
			maxFreqLabel = new NameValueBox("Max Freq (MHz)", "NaN");
			readingsCountLabel = new NameValueBox("Readings ", "NaN");
			minOccupancyLabel = new NameValueBox("Min Occupancy", "NaN");
			maxOccupancyLabel = new NameValueBox("Max Occupancy", "NaN");
			meanOccupancyLabel = new NameValueBox("Mean Occupancy", "NaN");
			selectionGrid.setWidget(0, 0, minFreqLabel);
			selectionGrid.setWidget(0, 1, maxFreqLabel);
			selectionGrid.setWidget(0, 2, dayCountField);
			selectionGrid.setWidget(0, 3, startDateCalendar);
			selectionGrid.setWidget(0, 4, userDayCountField);

			selectionGrid.setWidget(1, 0, minOccupancyLabel);
			selectionGrid.setWidget(1, 1, maxOccupancyLabel);
			selectionGrid.setWidget(1, 2, meanOccupancyLabel);
			selectionGrid.setWidget(1, 3, readingsCountLabel);
			selectionGrid.setWidget(1, 4, showStatisticsButton);

			verticalPanel.add(selectionGrid);
			startDateCalendar.setTitle("Start Date");

			showStatisticsButton.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(
						com.google.gwt.event.dom.client.ClickEvent event) {
					for (SensorMarker marker : sensorMarkers) {
						if (marker.isSelected()) {
							long startTime = marker.getSelectedStartTime();
							int days = marker.getDayCount();
							logger.finer("Day Count = " + days);
							if (days > 0) {
								new DailyStatsChart(spectrumBrowser,
										SpectrumBrowserShowDatasets.this,
										marker.getId(), 
										startTime,  days,
										marker.measurementType, verticalPanel,
										SpectrumBrowser.MAP_WIDTH,
										SpectrumBrowser.MAP_HEIGHT);
							}
						}
					}
				}

			});

			setSummaryUndefined();

			map = new MapWidget();
			map.setSize(SpectrumBrowser.MAP_WIDTH + "px",
					SpectrumBrowser.MAP_HEIGHT + "px");
			verticalPanel.add(map);

			spectrumBrowser.getSpectrumBrowserService().getLocationInfo(
					spectrumBrowser.getSessionId(),
					new SpectrumBrowserCallback<String>() {

						@Override
						public void onFailure(Throwable caught) {
							logger.log(Level.SEVERE,
									"Error in processing request", caught);
							spectrumBrowser.logoff();
						}

						@Override
						public void onSuccess(String jsonString) {

							try {
								logger.finer(jsonString);
								JSONObject jsonObj = (JSONObject) JSONParser
										.parseLenient(jsonString);
								JSONArray locationArray = jsonObj.get(
										"locationMessages").isArray();

								int nEntries = locationArray.size();
								double averageLat = 0;
								double averageLong = 0;

								logger.fine("Returned " + locationArray.size()
										+ " Location messages");

								for (int i = 0; i < locationArray.size(); i++) {
									JSONObject jsonObject = locationArray
											.get(i).isObject();
									double lon = jsonObject.get("Lon")
											.isNumber().doubleValue();
									double lat = jsonObject.get("Lat")
											.isNumber().doubleValue();

									averageLat += lat;
									averageLong += lon;

									LatLng point = LatLng.newInstance(lat, lon);

									String iconPath = SpectrumBrowser
											.getBaseUrl()
											+ "../icons/mm_20_red.png";
									logger.finer("lon = " + lon + " lat = "
											+ lat + " iconPath = " + iconPath);
									Icon icon = Icon.newInstance(iconPath);

									icon.setIconSize(Size.newInstance(12, 20));
									icon.setIconAnchor(Point.newInstance(6, 20));
									icon.setInfoWindowAnchor(Point.newInstance(
											5, 1));

									MarkerOptions options = MarkerOptions
											.newInstance();
									options.setIcon(icon);

									options.setClickable(true);
									SensorMarker marker = new SensorMarker(
											point, options, jsonObject);
									sensorMarkers.add(marker);
									marker.addMarkerClickHandler(new MarkerClickHandler() {

										@Override
										public void onClick(
												MarkerClickEvent event) {

											SensorMarker marker = (SensorMarker) event
													.getSender();
											if (map.getInfoWindow().isVisible()) {
												marker.closeInfoWindow();
												selectedMarkerId = marker
														.getId();

												for (SensorMarker m : sensorMarkers) {
													m.setSelected(false);
												}
												marker.setSelected(true);
												marker.showSummary();
												marker.showMapBlowup();
												return;
											} else {
												marker.setSelected(false);
												setSummaryUndefined();
											}

											InfoWindow info = map.getInfoWindow();
											
											info.open(marker, marker.getInfoWindowContent());

										}
									});

									averageLat /= nEntries;
									averageLong /= nEntries;
									map.addOverlay(marker);
									map.setCenter(LatLng.newInstance(
											averageLat, averageLong), 4);

								}

							} catch (Exception ex) {
								logger.log(Level.SEVERE, "Error ", ex);

							}
						}
					}

			);
		} catch (Exception ex) {
			logger.log(Level.SEVERE, "Error in displaying data sets", ex);
		}
	}

}
