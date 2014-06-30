package gov.nist.spectrumbrowser.client;

import java.util.Date;
import java.util.HashSet;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.core.client.JsDate;
import com.google.gwt.core.client.Scheduler;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.i18n.client.NumberFormat;
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
import com.google.gwt.user.client.ui.MenuItem;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.google.gwt.user.datepicker.client.DateBox;

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
	HashSet<FrequencyRange> frequencyRanges = new HashSet<FrequencyRange>();
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

	private MenuBar menuBar;

	private MenuBar selectFrequencyMenuBar;

	static Logger logger = Logger.getLogger("SpectrumBrowser");

	class FrequencyRange {
		long minFreq;
		long maxFreq;
		public FrequencyRange(long minFreq, long maxFreq) {
			this.minFreq = minFreq;
			this.maxFreq = maxFreq;
		}
		@Override 
		public boolean equals(Object that) {
			FrequencyRange thatRange = (FrequencyRange) that;
			return this.minFreq == thatRange.minFreq && this.maxFreq == thatRange.maxFreq;
		}
		
		@Override
		public int hashCode() {
			return  Long.toString(maxFreq + minFreq).hashCode();
			
		}
	}
	
	class SelectFreqCommand implements Scheduler.ScheduledCommand {
		private long minFreq;
		private long maxFreq;

		public SelectFreqCommand(long minFreq, long maxFreq) {
			this.minFreq = minFreq;
			this.maxFreq = maxFreq;
		}

		@Override
		public void execute() {
			boolean centered = false;
		
			for ( SensorMarker marker : sensorMarkers) {
				if ( minFreq == 0 && maxFreq == 0 ) {
					marker.setVisible(true);
					if (!centered) {
						map.setCenter(marker.getLatLng());
						centered = true;
					}
				} else if (marker.getMinFreq() == minFreq && marker.getMaxFreq() == maxFreq) {
					marker.setVisible(true);
					if (!centered) {
						map.setCenter(marker.getLatLng());
						centered = true;
					}
				} else {
					marker.setVisible(false);
				}
			}
		}
		
	}


	class SensorMarker extends Marker {
		private JSONObject locationMessageJsonObject;

		private String measurementType;

		
		private long tStart;
		private long tStartLocalTime;
		private String tStartLocalTimeFormattedTimeStamp;
		
		private long tSelectedStartTime;
		protected long tStartDayBoundary;
		private long dayBoundaryDelta;


		private boolean selected;
		private long tStartReadings;
		private long tEndReadings;
		private long tEndReadingsLocalTime;
		private String tEndLocalTImeFormattedTimeStamp;
		
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
		
		
		public void makeVisible(boolean visible) {
			this.setVisible(visible);
		}
		

		public void setSelected(boolean flag) {
			selected = flag;
			if (!flag) {
				String iconPath = SpectrumBrowser.getIconsPath()
						+ "mm_20_red.png";
				setImage(iconPath);
				selectedMarker = null;
			} else {
				String iconPath = SpectrumBrowser.getIconsPath()
						+ "mm_20_yellow.png";
				setImage(iconPath);
				selectedMarker = this;
			}
		}

		public boolean isSelected() {
			return selected;
		}

		private long getSelectedDayBoundary(long time) {
			JsDate jsDate = JsDate.create(time*1000);
			jsDate.setHours(0, 0, 0, 0);
			return (long) jsDate.getTime()/1000;
		}
		
	
		
		private void updateDataSummary(long startTime, int dayCount) {
			logger.fine("UpdateDataSummary " + startTime + " dayCount " + dayCount);
			String sessionId = spectrumBrowser.getSessionId();
			String sensorId = getId();
			String locationMessageId = locationMessageJsonObject.get("_id").isObject()
					.get("$oid").isString().stringValue();
			spectrumBrowser.getSpectrumBrowserService().getDataSummary(
					sessionId, sensorId, locationMessageId,
					startTime, dayCount, new SpectrumBrowserCallback<String>() {

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
									tStartDayBoundary = (long) jsonObj.get("tStartDayBoundary").isNumber().doubleValue();
									tSelectedStartTime = getSelectedDayBoundary((long) jsonObj.get("tStartDayBoundary").isNumber().doubleValue());
									dayBoundaryDelta = tStartDayBoundary - tSelectedStartTime; 
									tStartLocalTimeFormattedTimeStamp = jsonObj.get("tStartLocalTimeFormattedTimeStamp").isString().stringValue();
									logger.finer("tStartLocalTime " + tStartLocalTime);
									tEndReadingsLocalTime = (long) jsonObj
											.get("tEndReadingsLocalTime")
											.isNumber().doubleValue();
									tEndLocalTImeFormattedTimeStamp = jsonObj.get("tEndLocalTimeFormattedTimeStamp").isString().stringValue();

									
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
				tStart = (long) jsonObject.get("t").isNumber().doubleValue();
				tStartLocalTime = (long) jsonObject.get("tStartLocalTime").isNumber()
						.doubleValue();
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
								if (eventDate.getTime() <= getSelectedDayBoundary(tStartReadings)*1000 ) {
									startDateCalendar.getDatePicker().setValue(
											new Date(getSelectedDayBoundary(tStartReadings)));
									startDateCalendar
											.getDatePicker()
											.setCurrentMonth(
													new Date(
															getSelectedDayBoundary(tStartReadings)));
								} else if (eventDate.getTime() >= tEndReadings * 1000) {
									startDateCalendar
											.getDatePicker()
											.setValue(
													new Date(
															getSelectedDayBoundary(tEndReadings)));
									startDateCalendar
											.getDatePicker()
											.setCurrentMonth(new Date(
													getSelectedDayBoundary(tEndReadings)));
												

								} else {
									logger.finer("Date in acceptable range");
									tSelectedStartTime = getSelectedDayBoundary(eventDate.getTime() / 1000);
									startDateCalendar.getDatePicker().setValue(
											eventDate);
									startDateCalendar.getDatePicker().setCurrentMonth(eventDate);

									if (userDayCountField.isNonNegative()) {
										String dayCountString = userDayCountField
												.getValue();
										dayCount = Integer
												.parseInt(dayCountString);
										logger.finest("dayCount = " + dayCount);

										
										updateDataSummary(tSelectedStartTime + dayBoundaryDelta,
												dayCount);
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
					+ NumberFormat.getFormat("00.00").format(getLatLng().getLatitude())
					+ " Long = "
					+ NumberFormat.getFormat("00.00").format(getLatLng().getLongitude())
					+ " Alt = "
					+ formatToPrecision(2,getAlt())
					+ " Ft."		
					+ "<br/> Sensor ID = " + this.getId() + " Type = "
					+ measurementType
					+ " Start = "
					+ getTstartLocalTimeAsString()
					+ " End = "
					+ getTendReadingsLocalTimeAsString()
					+ "<br/>fStart = "
					+ dataSetMinFreq
					+ "MHz"
					+ " fStop = "
					+ dataSetMaxFreq
					+ "MHz"
					+ "<br/>Max Occupancy = "
					+ formatToPrecision(2, dataSetMaxOccupancy * 100)
					+ "%"
					+ " Min Occupancy = "
					+ formatToPrecision(2, dataSetMinOccupancy * 100)
					+ "%"
					+ "; Mean Occupancy = "
					+ formatToPrecision(2, dataSetMeanOccupancy * 100)
					+ "%"
					+ "<br/>Acquisition Count = " + dataSetReadingsCount + "<br/><br/></div>";
		}

		public String getTstartLocalTimeAsString() {
			return tStartLocalTimeFormattedTimeStamp;
		}

		

		public String getTendReadingsLocalTimeAsString() {
			return tEndLocalTImeFormattedTimeStamp;
		}

		public String getId() {
			return locationMessageJsonObject.get("SensorID").isString().stringValue();

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
						
						updateDataSummary(tSelectedStartTime, userSelectedDayCount);
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
	
		
	private void populateMenuItems() {

	

		MenuItem menuItem = new MenuItem(new SafeHtmlBuilder().appendEscaped("Log Off").toSafeHtml(),
				new Scheduler.ScheduledCommand() {

			@Override
			public void execute() {
				spectrumBrowser.logoff();

			}
		});
		
		menuBar.addItem(menuItem);
	

		
		selectFrequencyMenuBar = new MenuBar(true);

		menuItem = new MenuItem(new SafeHtmlBuilder().appendEscaped("Select All").toSafeHtml(), 
				new SelectFreqCommand(0,0));
		selectFrequencyMenuBar.addItem(menuItem);
	
		for (FrequencyRange f : frequencyRanges) {
			 menuItem = new MenuItem(new SafeHtmlBuilder().appendEscaped
					(Long.toString(f.minFreq) + " - " + Long.toString(f.maxFreq) + " MHz").toSafeHtml()
					, new SelectFreqCommand(f.minFreq,f.maxFreq));
		
			selectFrequencyMenuBar.addItem(menuItem);
		}
		menuBar.addItem("Select Frequency Band",selectFrequencyMenuBar);

		menuItem = new MenuItem(new SafeHtmlBuilder().appendEscaped("Help")
				.toSafeHtml(), new Scheduler.ScheduledCommand() {

			@Override
			public void execute() {

			}
		});
		
		menuBar.addItem(menuItem);

		menuItem = new MenuItem(new SafeHtmlBuilder().appendEscaped("About")
				.toSafeHtml(), new Scheduler.ScheduledCommand() {

			@Override
			public void execute() {
				// TODO

			}
		});
		menuBar.addItem(menuItem);

	}

	public void buildUi() {
		try {

			verticalPanel.clear();
			menuBar = new MenuBar();
			menuBar.clearItems();
		
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
							long startTime = marker.getSelectedStartTime() + marker.dayBoundaryDelta;
							int days = marker.getDayCount();
							logger.finer("Day Count = " + days + " startTime = " + startTime);
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

										logger.fine("Returned " + locationArray.size()
										+ " Location messages");
								boolean centered = false;

								for (int i = 0; i < locationArray.size(); i++) {
									JSONObject jsonObject = locationArray
											.get(i).isObject();
									double lon = jsonObject.get("Lon")
											.isNumber().doubleValue();
									double lat = jsonObject.get("Lat")
											.isNumber().doubleValue();
									
									long minFreq = (long)jsonObject.get("minFreq").isNumber().doubleValue()/1000000;
									long maxFreq = (long)jsonObject.get("maxFreq").isNumber().doubleValue()/1000000;
									FrequencyRange freqRange = new FrequencyRange(minFreq,maxFreq);
									frequencyRanges.add(freqRange);

							
									LatLng point = LatLng.newInstance(lat, lon);

									String iconPath = SpectrumBrowser
											.getIconsPath()
											+ "mm_20_red.png";
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
												map.setCenter(LatLng.newInstance(
														marker.getLatLng().getLatitude(), 
														marker.getLatLng().getLongitude()), 4);

												return;
											} else {
												marker.setSelected(false);
												setSummaryUndefined();
											}

											InfoWindow info = map.getInfoWindow();
											
											info.open(marker, marker.getInfoWindowContent());

										}
									});

									map.addOverlay(marker);
									if (! centered) {
										map.setCenter(marker.getLatLng(), 4);
										centered = true;
									}


								}
								populateMenuItems();
								
								


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
