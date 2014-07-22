package gov.nist.spectrumbrowser.client;

import java.util.Date;
import java.util.HashSet;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.core.client.JsDate;
import com.google.gwt.core.client.Scheduler;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.i18n.client.DateTimeFormat;
import com.google.gwt.i18n.client.DateTimeFormat.PredefinedFormat;
import com.google.gwt.i18n.client.NumberFormat;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.maps.client.InfoWindow;
import com.google.gwt.maps.client.InfoWindowContent;
import com.google.gwt.maps.client.MapWidget;
import com.google.gwt.maps.client.Maps;
import com.google.gwt.maps.client.event.MarkerClickHandler;
import com.google.gwt.maps.client.event.MarkerMouseOutHandler;
import com.google.gwt.maps.client.event.MarkerMouseOverHandler;
import com.google.gwt.maps.client.geom.LatLng;
import com.google.gwt.maps.client.geom.Point;
import com.google.gwt.maps.client.geom.Size;
import com.google.gwt.maps.client.overlay.Icon;
import com.google.gwt.maps.client.overlay.Marker;
import com.google.gwt.maps.client.overlay.MarkerOptions;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.DialogBox;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.MenuBar;
import com.google.gwt.user.client.ui.MenuItem;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.google.gwt.user.datepicker.client.DateBox;
import com.googlecode.gwt.charts.client.format.DateFormat;

public class SpectrumBrowserShowDatasets {
	public static final String END_LABEL = "Select Data Set";

	public static final String LABEL = END_LABEL + " >>";

	private static final long SECONDS_PER_DAY = 24 * 60 * 60;

	private SpectrumBrowser spectrumBrowser;
	private VerticalPanel verticalPanel;
	private MapWidget map;
	private HashSet<SensorMarker> sensorMarkers = new HashSet<SensorMarker>();
	private HashSet<FrequencyRange> globalFrequencyRanges = new HashSet<FrequencyRange>();
	private SensorMarker selectedMarker;
	private Grid selectionGrid;

	private HorizontalPanel sensorInfoPanel;

	private MenuBar navigationBar;

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
			return this.minFreq == thatRange.minFreq
					&& this.maxFreq == thatRange.maxFreq;
		}

		@Override
		public int hashCode() {
			return Long.toString(maxFreq + minFreq).hashCode();
		}

		@Override
		public String toString() {
			return Double.toString((double) minFreq / 1000000.0) + " MHz - "
					+ Double.toString((double) (maxFreq / 1000000.0)) + " MHz";
		}
	}

	class SelectFreqCommand implements Scheduler.ScheduledCommand {
		private FrequencyRange freqRange;

		public SelectFreqCommand(long minFreq, long maxFreq) {
			this.freqRange = new FrequencyRange(minFreq, maxFreq);
		}

		@Override
		public void execute() {
			boolean centered = false;

			for (SensorMarker marker : sensorMarkers) {
				if (freqRange.minFreq == 0 && freqRange.maxFreq == 0) {
					marker.setVisible(true);
					if (!centered) {
						map.setCenter(marker.getLatLng());
						centered = true;
					}
				} else if (marker.getFrequencyRanges().contains(this.freqRange)) {
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
		private DateBox startDateCalendar;
		private MenuBar runLengthMenuBar;
		private Button showStatisticsButton;
		private Button showSensorDataButton;
		private MenuBar userDayCountMenuBar;
		private Label userDayCountLabel;
		private MenuBar selectFrequency;
		private MenuBar sensorSelectFrequency;
		private Label sensorSelectFrequencyLabel;

		private String measurementType;

		private long tStart;
		private long tStartLocalTime;
		private String tStartLocalTimeFormattedTimeStamp;

		private long tSelectedStartTime = -1;
		protected long tStartDayBoundary;
		private long dayBoundaryDelta = 0;

		private boolean selected;
		private long tStartReadings;
		private long tEndReadings;
		private long tEndReadingsLocalTime;
		private String tEndLocalTimeFormattedTimeStamp;

		private long tAquisitionStart;
		private long tAquisitionEnd;

		private double maxOccupancy;
		private double minOccupancy;
		private double meanOccupancy;
		private double dataSetMaxOccupancy;
		private double dataSetMinOccupancy;
		private double dataSetMeanOccupancy;
		private long readingsCount;
		private long dataSetReadingsCount;
		private int availableDayCount; // Max number of days available.
		private boolean firstUpdate = true;
		private int dayCount = -1;
		private InfoWindowContent iwc;
		private HashSet<FrequencyRange> frequencyRanges = new HashSet<FrequencyRange>();
		private long minFreq = -1;
		private long maxFreq = -1;
		private String dataSetAcquistionStartLocalTime;
		private String dataSetAcquistionEndLocalTime;
		private boolean firstSummaryUpdate = true;
		private String tAcquisitionStartFormattedTimeStamp;
		private String tAcquisitionEndFormattedTimeStamp;

		private HTML info;

		class SensorSelectFreqCommand implements Scheduler.ScheduledCommand {
			FrequencyRange freqRange;

			SensorSelectFreqCommand(FrequencyRange frequencyRange) {
				this.freqRange = frequencyRange;
			}

			@Override
			public void execute() {
				SensorMarker.this.minFreq = freqRange.minFreq;
				SensorMarker.this.maxFreq = freqRange.maxFreq;
				sensorSelectFrequencyLabel.setText(freqRange.toString());
				updateDataSummary();
			}

		}

		class SelectUserDayCountCommand implements Scheduler.ScheduledCommand {

			private int dc;

			public SelectUserDayCountCommand(int dayCount) {
				this.dc = dayCount;
			}

			@Override
			public void execute() {
				SensorMarker.this.setDayCount(dc);
				updateDataSummary();
			}

		}

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
				selectionGrid.remove(startDateCalendar);
				selectionGrid.remove(sensorSelectFrequency);
				firstSummaryUpdate = true;
				selectionGrid.remove(runLengthMenuBar);
				selectionGrid.remove(userDayCountLabel);
				selectionGrid.remove(sensorSelectFrequencyLabel);
				selectionGrid.remove(showSensorDataButton);
			} else {
				String iconPath = SpectrumBrowser.getIconsPath()
						+ "mm_20_yellow.png";
				setImage(iconPath);
				selectedMarker = this;
				selectionGrid.setWidget(0, 0, startDateCalendar);
				selectionGrid.setWidget(0, 1, runLengthMenuBar);
				selectionGrid.setWidget(0,2,userDayCountLabel);
				selectionGrid.setWidget(0, 3, selectFrequency);
				selectionGrid.setWidget(0,4,sensorSelectFrequencyLabel);
				selectionGrid.setWidget(0, 5, showStatisticsButton);
				if (measurementType.equals("FFT-Power")) {
					selectionGrid.setWidget(0,6,showSensorDataButton);
				}
			}

		}

		public HashSet<FrequencyRange> getFrequencyRanges() {
			return this.frequencyRanges;
		}

		public boolean isSelected() {
			return selected;
		}

		private long getSelectedDayBoundary(long time) {
			JsDate jsDate = JsDate.create(time * 1000);
			jsDate.setHours(0, 0, 0, 0);
			return (long) jsDate.getTime() / 1000;
		}

		private String getFormattedDate(long timeSeconds) {
			DateTimeFormat dateTimeFormat = DateTimeFormat
					.getFormat(PredefinedFormat.DATE_SHORT);
			return dateTimeFormat.format(new Date(timeSeconds * 1000));
		}

		private void updateDataSummary() {
			// Convert the selected start time to utc
			long startTime = getSelectedStartTime() + dayBoundaryDelta;
			logger.fine("UpdateDataSummary " + startTime + " dayCount "
					+ getDayCount());
			String sessionId = spectrumBrowser.getSessionId();
			String sensorId = getId();
			String locationMessageId = locationMessageJsonObject.get("_id")
					.isObject().get("$oid").isString().stringValue();
			spectrumBrowser.getSpectrumBrowserService().getDataSummary(
					sessionId, sensorId, locationMessageId, startTime,
					getDayCount(), minFreq, maxFreq,
					new SpectrumBrowserCallback<String>() {

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
									Window.alert("No data found!");
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

								tAquisitionStart = (long) jsonObj
										.get("tAquistionStart").isNumber()
										.doubleValue();
								tAquisitionEnd = (long) jsonObj
										.get("tAquisitionEnd").isNumber()
										.doubleValue();
								tAcquisitionStartFormattedTimeStamp = jsonObj
										.get("tAquisitionStartFormattedTimeStamp")
										.isString().stringValue();
								tAcquisitionEndFormattedTimeStamp = jsonObj
										.get("tAquisitionEndFormattedTimeStamp")
										.isString().stringValue();
								tEndReadings = (long) jsonObj
										.get("tEndReadings").isNumber()
										.doubleValue();

								maxOccupancy = jsonObj.get("maxOccupancy")
										.isNumber().doubleValue();
								minOccupancy = jsonObj.get("minOccupancy")
										.isNumber().doubleValue();
								meanOccupancy = jsonObj.get("meanOccupancy")
										.isNumber().doubleValue();
								logger.finer("meanOccupancy" + meanOccupancy);
								tStartLocalTime = (long) jsonObj
										.get("tStartLocalTime").isNumber()
										.doubleValue();
								tStartDayBoundary = (long) jsonObj
										.get("tStartDayBoundary").isNumber()
										.doubleValue();
								setSelectedStartTime(tStartDayBoundary);
								dayBoundaryDelta = tStartDayBoundary
										- getSelectedDayBoundary((long) jsonObj
												.get("tStartDayBoundary")
												.isNumber().doubleValue());
								tStartLocalTimeFormattedTimeStamp = jsonObj
										.get("tStartLocalTimeFormattedTimeStamp")
										.isString().stringValue();
								logger.finer("tStartLocalTime "
										+ tStartLocalTime);
								tEndReadingsLocalTime = (long) jsonObj
										.get("tEndReadingsLocalTime")
										.isNumber().doubleValue();
								tEndLocalTimeFormattedTimeStamp = jsonObj
										.get("tEndLocalTimeFormattedTimeStamp")
										.isString().stringValue();
								logger.finer("tEndReadings " + tEndReadings);
								availableDayCount = (int) ((double)(tEndReadings - getSelectedDayBoundary(tStartReadings)) / (double)SECONDS_PER_DAY + 0.5);

								if (firstUpdate) {
									firstUpdate = false;

									logger.finer("availableDayCount "
											+ availableDayCount);
									dataSetReadingsCount = readingsCount;
									dataSetMaxOccupancy = maxOccupancy;
									dataSetMinOccupancy = minOccupancy;
									dataSetMeanOccupancy = meanOccupancy;
									dataSetAcquistionStartLocalTime = tStartLocalTimeFormattedTimeStamp;
									dataSetAcquistionEndLocalTime = tEndLocalTimeFormattedTimeStamp;

								} else {
									// Otherwise, immediately show the updates
									// of summary data.
									showSummary();
								}
							} catch (Throwable ex) {
								logger.log(Level.SEVERE,
										"Error Parsing returned data ", ex);
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
				startDateCalendar = new DateBox();
				startDateCalendar.setTitle("Start Date");
				showStatisticsButton = new Button("Daily Occupancy");
				showStatisticsButton
						.setTitle("Click to generate daily occupancy chart");
				runLengthMenuBar = new MenuBar(true);
				userDayCountMenuBar = new MenuBar(true);
				userDayCountLabel = new Label();
				selectFrequency = new MenuBar(true);
				sensorSelectFrequency = new MenuBar(true);
				sensorSelectFrequencyLabel = new Label();
				selectFrequency.addItem("Freq Band", sensorSelectFrequency);
				userDayCountMenuBar = new MenuBar(true);
				runLengthMenuBar
						.addItem("Duration (days)", userDayCountMenuBar);

				showStatisticsButton.addClickHandler(new ClickHandler() {

					@Override
					public void onClick(
							com.google.gwt.event.dom.client.ClickEvent event) {
						if (isSelected()) {
							long startTime = getSelectedStartTime()
									+ dayBoundaryDelta;
							int days = getDayCount();
							logger.finer("Day Count = " + days
									+ " startTime = " + startTime);
							if (days > 0) {
								new DailyStatsChart(spectrumBrowser,
										SpectrumBrowserShowDatasets.this,
										getId(), startTime, days, getMinFreq(),
										getMaxFreq(), measurementType,
										verticalPanel,
										SpectrumBrowser.MAP_WIDTH,
										SpectrumBrowser.MAP_HEIGHT);
							}
						}
					}

				});
				
				showSensorDataButton = new Button("Current Readings");
				
				showSensorDataButton.addClickHandler( new ClickHandler() {

					@Override
					public void onClick(ClickEvent event) {
						new SensorDataStream(getId(),verticalPanel,spectrumBrowser,SpectrumBrowserShowDatasets.this);
					}});
				
				

				this.locationMessageJsonObject = jsonObject;
				// Extract the data values.
				tStart = (long) jsonObject.get("t").isNumber().doubleValue();
				tStartLocalTime = (long) jsonObject.get("tStartLocalTime")
						.isNumber().doubleValue();
				updateDataSummary();

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
								if (eventDate.getTime() <= getSelectedDayBoundary(tAquisitionStart) * 1000) {
									setSelectedStartTime(getSelectedDayBoundary(tAquisitionStart));
									updateDataSummary();
								} else if (eventDate.getTime() >= tAquisitionEnd * 1000) {
									setSelectedStartTime(getSelectedDayBoundary(tAquisitionStart));
									updateDataSummary();

								} else {
									logger.finer("Date in acceptable range");
									setSelectedStartTime(getSelectedDayBoundary(eventDate
											.getTime() / 1000));
									updateDataSummary();
								}

							}
						});

			} catch (Exception ex) {
				logger.log(Level.SEVERE, "Error creating sensor marker", ex);
				spectrumBrowser.displayError("Internal error creating marker");
			}
		}

		public double getAlt() {
			return locationMessageJsonObject.get("Alt").isNumber()
					.doubleValue();
		}

		public String getInfo() {

			return "<b color=\"red\" > Click on marker to select sensor. </b>"
					+ "<div align=\"left\", height=\"300px\">"
					+ "<br/>sensor ID = "
					+ getId()
					+ "<br/>Lat = "
					+ NumberFormat.getFormat("00.00").format(
							getLatLng().getLatitude())
					+ " Long = "
					+ NumberFormat.getFormat("00.00").format(
							getLatLng().getLongitude())
					+ " Alt = "
					+ formatToPrecision(2, getAlt())
					+ " Ft."
					+ "<br/> Sensor ID = "
					+ this.getId()
					+ " Type = "
					+ measurementType
					+ "<br/> Start = "
					+ dataSetAcquistionStartLocalTime
					+ " End = "
					+ dataSetAcquistionEndLocalTime
					+ "<br/>freqRanges = "
					+ getFormattedFrequencyRanges()
					+ "Max Occupancy = "
					+ formatToPrecision(2, dataSetMaxOccupancy * 100)
					+ "%"
					+ " Min Occupancy = "
					+ formatToPrecision(2, dataSetMinOccupancy * 100)
					+ "%"
					+ "; Mean Occupancy = "
					+ formatToPrecision(2, dataSetMeanOccupancy * 100)
					+ "%"
					+ "<br/>Acquisition Count = "
					+ dataSetReadingsCount
					+ "<br/><br/></div>";
		}

		private String getFormattedFrequencyRanges() {
			StringBuilder retval = new StringBuilder();
			for (FrequencyRange r : globalFrequencyRanges) {
				retval.append(r.toString() + " <br/>");
			}
			return retval.toString();
		}

		public String getTstartLocalTimeAsString() {
			return dataSetAcquistionStartLocalTime;
		}

		public String getTendReadingsLocalTimeAsString() {
			return dataSetAcquistionEndLocalTime;
		}

		public String getId() {
			return locationMessageJsonObject.get("SensorID").isString()
					.stringValue();

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
			try {
				if (firstSummaryUpdate) {
					firstSummaryUpdate = false;
					sensorSelectFrequency.clearItems();
					boolean firstItem = true;
					for (FrequencyRange r : frequencyRanges) {
						MenuItem menuItem = new MenuItem(new SafeHtmlBuilder()
								.appendEscaped(r.toString()).toSafeHtml(),
								new SensorSelectFreqCommand(r));
						if (firstItem) {
							this.minFreq = r.minFreq;
							this.maxFreq = r.maxFreq;
							sensorSelectFrequencyLabel.setText(new FrequencyRange(minFreq,maxFreq).toString());
						}
						sensorSelectFrequency.addItem(menuItem);
					}
					updateDataSummary();
				}

				String sid = getId();
				String minOccupancyVal = formatToPrecision(2,
						minOccupancy * 100) + "%";
				String maxOccupancyVal = formatToPrecision(2,
						maxOccupancy * 100) + "%";
				String meanOccupancyVal = formatToPrecision(2,
						meanOccupancy * 100) + "%";

				int rcount = (int) readingsCount;

				sensorInfoPanel.clear();
				startDateCalendar.setEnabled(true);
				final int maxDayCount = (int)( (double)(tAquisitionEnd - getSelectedStartTime()) / (double)SECONDS_PER_DAY + .5);

				final int allowableDayCount = measurementType
						.equals("FFT-Power") ? Math.min(14, maxDayCount) : Math
						.min(30, maxDayCount);
				userDayCountMenuBar.clearItems();
				for (int i = 0; i < allowableDayCount; i++) {
					MenuItem menuItem = new MenuItem(Integer.toString(i + 1),
							new SelectUserDayCountCommand(i + 1));
					userDayCountMenuBar.addItem(menuItem);
				}
				if (dayCount == -1 || dayCount > allowableDayCount) {
					setDayCount(allowableDayCount);
				}
				info = new HTML(
						"<b>Sensor ID: "
								+ sid
								+ "; Measurement Type :"
								+ measurementType
								+ "<br/> Available Period: "
								+ tAcquisitionStartFormattedTimeStamp
								+ " to "
								+ tAcquisitionEndFormattedTimeStamp
								+ " Available acquisition count: "
								+ dataSetReadingsCount
								+ "<br/>"
								+ "<br/>Selected Frequency Band : "
								+ new FrequencyRange(minFreq, maxFreq)
										.toString()
								+ "; Selected start date: "
								+ getFormattedDate(getSelectedDayBoundary(getSelectedStartTime()))
								+ "; Duration: " + getDayCount()
								+ " days; Acquistion count in interval: "
								+ rcount
								+ "<br/>Min channel occupancy in interval: "
								+ minOccupancyVal
								+ "; Max channel occupancy in interval: "
								+ maxOccupancyVal
								+ "; Mean channel occupancy in interval: "
								+ meanOccupancyVal + "</b>");
				info.setStyleName("sensorInfo");
				sensorInfoPanel.add(info);
				

				if (rcount > 0) {
					showStatisticsButton.setEnabled(true);
				} else {
					Window.alert("No aquisitions found in selected interval. Please choose another.");
				}
			} catch (Exception ex) {
				logger.log(Level.SEVERE, "Error in updating data summary ", ex);
			}

		}

		public long getSelectedStartTime() {
			return this.tSelectedStartTime;
		}

		private void setDayCount(int dayCount) {
			logger.finer("setDayCount: " + dayCount);
			this.dayCount = dayCount;
			userDayCountLabel.setText(Integer.toString(dayCount));
		}

		public int getDayCount() {
			return this.dayCount;
		}

		public InfoWindowContent getInfoWindowContent() {
			return iwc;
		}

		public void setFrequencyRanges(HashSet<FrequencyRange> freqRanges) {
			FrequencyRange selectedFreqRange = freqRanges.iterator().next();
			this.minFreq = selectedFreqRange.minFreq;
			this.maxFreq = selectedFreqRange.maxFreq;
			this.frequencyRanges.addAll(freqRanges);
		}

		private void setSelectedStartTime(long tSelectedStartTime) {
			logger.finer("setSelectedStartTime: " + tSelectedStartTime);
			this.tSelectedStartTime = tSelectedStartTime;
			startDateCalendar.setValue(new Date(
					getSelectedDayBoundary(tSelectedStartTime) * 1000));
			startDateCalendar.getDatePicker().setValue(
					new Date(getSelectedDayBoundary(tSelectedStartTime)));
			startDateCalendar.getDatePicker().setCurrentMonth(
					new Date(getSelectedDayBoundary(tSelectedStartTime)));

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
		sensorInfoPanel.clear();

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

		MenuItem menuItem = new MenuItem(new SafeHtmlBuilder().appendEscaped(
				"Log Off").toSafeHtml(), new Scheduler.ScheduledCommand() {

			@Override
			public void execute() {
				spectrumBrowser.logoff();

			}
		});

		navigationBar.addItem(menuItem);

		selectFrequencyMenuBar = new MenuBar(true);

		menuItem = new MenuItem(new SafeHtmlBuilder().appendEscaped(
				"Select All").toSafeHtml(), new SelectFreqCommand(0, 0));
		selectFrequencyMenuBar.addItem(menuItem);

		for (FrequencyRange f : globalFrequencyRanges) {
			menuItem = new MenuItem(new SafeHtmlBuilder().appendEscaped(
					Double.toString(f.minFreq/1E6) + " - " + Double.toString(f.maxFreq/1E6)
							+ " MHz").toSafeHtml(), new SelectFreqCommand(
					f.minFreq, f.maxFreq));

			selectFrequencyMenuBar.addItem(menuItem);
		}
		navigationBar.addItem("Select Markers By Frequency Band",
				selectFrequencyMenuBar);

		menuItem = new MenuItem(new SafeHtmlBuilder().appendEscaped("Help")
				.toSafeHtml(), new Scheduler.ScheduledCommand() {

			@Override
			public void execute() {

			}
		});

		navigationBar.addItem(menuItem);

		menuItem = new MenuItem(new SafeHtmlBuilder().appendEscaped("About")
				.toSafeHtml(), new Scheduler.ScheduledCommand() {

			@Override
			public void execute() {
				// TODO

			}
		});
		navigationBar.addItem(menuItem);

	}

	public void buildUi() {
		try {

			verticalPanel.clear();
			navigationBar = new MenuBar();
			navigationBar.clearItems();

			verticalPanel
					.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);

			verticalPanel.add(navigationBar);

			HTML html = new HTML("<h2>Select Sensor and Freq. Band</h2>", true);
			verticalPanel.add(html);

			sensorInfoPanel = new HorizontalPanel();
			verticalPanel.add(sensorInfoPanel);

			selectionGrid = new Grid(1, 7);
			selectionGrid.setStyleName("selectionGrid");

			verticalPanel.add(selectionGrid);

			setSummaryUndefined();

			map = new MapWidget();
			map.setTitle("Click on marker to select sensor");
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

									JSONArray sensorFreqs = jsonObject.get(
											"sensorFreq").isArray();
									HashSet<FrequencyRange> freqRanges = new HashSet<FrequencyRange>();
									for (int j = 0; j < sensorFreqs.size(); j++) {
										String minMaxFreq[] = sensorFreqs
												.get(j).isString()
												.stringValue().split(":");
										long minFreq = Long
												.parseLong(minMaxFreq[0]);
										long maxFreq = Long
												.parseLong(minMaxFreq[1]);
										FrequencyRange freqRange = new FrequencyRange(
												minFreq, maxFreq);
										freqRanges.add(freqRange);
										globalFrequencyRanges.add(freqRange);
									}

									LatLng point = LatLng.newInstance(lat, lon);

									String iconPath = SpectrumBrowser
											.getIconsPath() + "mm_20_red.png";
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
									marker.setFrequencyRanges(freqRanges);
									sensorMarkers.add(marker);

									marker.addMarkerMouseOverHandler(new MarkerMouseOverHandler() {

										@Override
										public void onMouseOver(
												MarkerMouseOverEvent event) {
											SensorMarker marker = (SensorMarker) event
													.getSender();
											InfoWindow info = map
													.getInfoWindow();

											info.open(marker, marker
													.getInfoWindowContent());
										}
									});

									marker.addMarkerMouseOutHandler(new MarkerMouseOutHandler() {

										@Override
										public void onMouseOut(
												MarkerMouseOutEvent event) {
											SensorMarker marker = (SensorMarker) event
													.getSender();
											marker.closeInfoWindow();

										}
									});

									marker.addMarkerClickHandler(new MarkerClickHandler() {

										@Override
										public void onClick(
												MarkerClickEvent event) {
											for (SensorMarker m : sensorMarkers) {
												m.setSelected(false);
											}
											SensorMarker marker = (SensorMarker) event
													.getSender();
											marker.setSelected(true);
											marker.showSummary();
											// marker.showMapBlowup();
											map.setCenter(LatLng.newInstance(
													marker.getLatLng()
															.getLatitude(),
													marker.getLatLng()
															.getLongitude()), 4);

										}
									});

									map.addOverlay(marker);
									if (!centered) {
										map.setCenter(marker.getLatLng(), 4);
										centered = true;
									}

								}
								populateMenuItems();

							} catch (Exception ex) {
								logger.log(Level.SEVERE, "Error ", ex);
								spectrumBrowser
										.displayError("Error parsing json response");

							}
						}
					}

			);
		} catch (Exception ex) {
			logger.log(Level.SEVERE, "Error in displaying data sets", ex);
		}
	}

}
